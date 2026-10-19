#!/usr/bin/env python3
"""Build the starter-database seed from the backend database, with no phone involved.

The app's static sync (publishers, series, creators, characters, bonds) takes thousands of paged
requests. The seed is one ready-made copy of the app's own database that the phone downloads and
imports on first run, so its sync only has to catch up. It is served at /db_query/seed/meta and
/db_query/seed/db (see db_query/seed.py).

This reads the same models, in the same way and with the same conversions, that the paged sync's
endpoints and the app use, and writes a Room database: tools/seed_template.sql has its tables, and
the data is filled in here. Run it again whenever the backend database changes.

  ENV_FILE=.env tools/build_seed_from_db.py [--out DIR] [--date YYYY-MM-DD]

Output goes to seed/ (or --out): seed.db.gz, meta.json and page_index.json (the ids the paged-sync
endpoints answer from; see db_query/page_index.py). The same data gives the same file apart
from the date rows are stamped with, which --date fixes.
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from datetime import date, datetime

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gcd_server.settings')

CHUNK = 5000
LONG_MAX = 2 ** 63 - 1


def django_setup():
    import django
    django.setup()


# ---- conversions: what the app does with each row of the paged sync (database/models/GcdJson.kt) ----

def year_date(year):
    """LocalDate.of(year, 1, 1) as Room stores it: java.time writes years past 9999 with a '+'."""
    if year > 9999:
        return f'+{year}-01-01'
    return f'{year:04d}-01-01' if year >= 0 else f'-{abs(year):04d}-01-01'


MIN_YEAR = -999999999  # LocalDate.MIN.year: what a series with no year began gets


def blank_to_none(s):
    return None if s is None or s == '' else s


def issue_date(text):
    """Issue.formatDate: '-00' means January or the first, a bad day falls back to the year."""
    if not text:
        return None
    new = text.replace('-00', '-01')
    for candidate in (new, new + '-01', new[:4] + '-01-01'):
        try:
            return datetime.strptime(candidate, '%Y-%m-%d').date().isoformat()
        except ValueError:
            continue
    return None


def int_from_string(s):
    first = re.split(r'[\s(\[{]', s)[0]
    return int(first) if re.fullmatch(r'[+-]?\d+', first) else 1


def long_or_none(s):
    if re.fullmatch(r'[+-]?\d+', s or ''):
        n = int(s)
        if -LONG_MAX - 1 <= n <= LONG_MAX:
            return n
    return None


def publisher_row(pk, f, today):
    return dict(publisherId=pk, publisher=f['name'],
                yearBegan=year_date(f['year_began']) if f['year_began'] is not None else None,
                yearBeganUncertain=int(f['year_began_uncertain'] == 1),
                yearEnded=year_date(f['year_ended']) if f['year_ended'] is not None else None,
                yearEndedUncertain=int(f['year_ended_uncertain'] == 1),
                url=blank_to_none(f['url']), lastUpdated=today)


def series_row(pk, f, today):
    return dict(seriesId=pk, seriesName=f['name'], sortName=f['sort_name'], volume=1,
                publisher=f['publisher'],
                startDate=year_date(f['year_began'] if f['year_began'] is not None else MIN_YEAR),
                endDate=year_date(f['year_ended']) if f['year_ended'] is not None else None,
                description=blank_to_none(f['tracking_notes']),
                publishingFormat=blank_to_none(f['publishing_format']),
                firstIssue=f['first_issue'], notes=blank_to_none(f['notes']),
                issueCount=f['issue_count'], lastUpdated=today)


def creator_row(pk, f, today):
    return dict(creatorId=pk, name=f['gcd_official_name'], sortName=f['sort_name'],
                bio=blank_to_none(f['bio']), lastUpdated=today)


def name_detail_row(pk, f, today):
    return dict(nameDetailId=pk, creator=f['creator'], name=f['name'],
                sortName=blank_to_none(f['sort_name']), lastUpdated=today)


def character_row(pk, f, today):
    return dict(characterId=pk, name=f['name'], alterEgo=f['alter_ego'], publisher=f['publisher'],
                lastUpdated=today)


def role_row(pk, f, today):
    return dict(roleId=pk, roleName=f['name'], sortOrder=f['sort_code'], lastUpdated=today)


def story_type_row(pk, f, today):
    return dict(storyTypeId=pk, name=f['name'], sortCode=f['sort_code'], lastUpdated=today)


def bond_type_row(pk, f, today):
    return dict(bondTypeId=pk, name=f['name'], description=f['description'], notes=f['notes'],
                lastUpdated=today)


def series_bond_row(pk, f, today):
    return dict(bondId=pk, origin=f['origin'], target=f['target'], originIssue=f['origin_issue'],
                targetIssue=f['target_issue'], bondType=f['bond_type'], notes=f['notes'],
                lastUpdated=today)


def issue_row(pk, f, today):
    return dict(issueId=pk, series=f['series'], issueNum=int_from_string(f['number']),
                releaseDate=issue_date(f['on_sale_date']), upc=long_or_none(f['barcode']),
                variantName=f['variant_name'], variantOf=f['variant_of'], sortCode=f['sort_code'],
                coverDateLong=blank_to_none(f['publication_date']),
                onSaleDateUncertain=int(f['on_sale_date_uncertain'] == 1),
                coverDate=issue_date(f['key_date']), notes=blank_to_none(f['notes']),
                issueNumRaw=f['number'], lastUpdated=today)


def serialized(queryset):
    """The queryset's rows as the endpoints send them (views.StandardResponse), in chunks."""
    from django.core.serializers import serialize
    ids = list(queryset.order_by('pk').values_list('pk', flat=True))
    model = queryset.model
    for i in range(0, len(ids), CHUNK):
        chunk = model.objects.filter(pk__in=ids[i:i + CHUNK]).order_by('pk')
        for item in json.loads(serialize('json', chunk, use_natural_foreign_keys=True)):
            yield item['pk'], item['fields']


def insert(con, table, rows):
    rows = list(rows)
    if not rows:
        return 0
    cols = list(rows[0])
    con.executemany(
        f'INSERT OR IGNORE INTO `{table}` ({", ".join(cols)}) VALUES ({", ".join("?" * len(cols))})',
        [tuple(r[c] for c in cols) for r in rows])
    return len(rows)


SKIPPED_TABLES = ('android_metadata', 'sqlite_sequence', 'room_master_table')


def content_hash(con):
    """A fingerprint of the tables and rows. The file itself is laid out differently by different
    SQLite versions, so its bytes say nothing about whether the data changed."""
    sha = hashlib.sha256()
    for name, sql in con.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
            "AND name != 'android_metadata' ORDER BY name"):
        sha.update(sql.encode())
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        if name in SKIPPED_TABLES or name.startswith('sqlite_'):
            continue
        sha.update(name.encode())
        for row in con.execute(f'SELECT * FROM "{name}" ORDER BY 1'):
            sha.update(repr(row).encode())
    return sha.hexdigest()[:12]


def num_pages(model):
    from db_query.views import ROWS_PER_PAGE
    return model.objects.all().count() // ROWS_PER_PAGE + 1


def build(db_path, today):
    from db_query.models import (GcdCharacter, GcdCreator, GcdCreatorNameDetail, GcdCreditType,
                                 GcdIssue, GcdPublisher, GcdSeries, GcdSeriesBond,
                                 GcdSeriesBondType, GcdStoryType)

    template = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_template.sql')).read()
    con = sqlite3.connect(db_path)
    con.executescript(template)
    con.execute('PRAGMA foreign_keys=OFF')

    def rows(model, convert, queryset=None):
        return (convert(pk, f, today) for pk, f in serialized(queryset or model.objects.all()))

    insert(con, 'Publisher', rows(GcdPublisher, publisher_row))
    insert(con, 'Role', rows(GcdCreditType, role_row))
    insert(con, 'StoryType', rows(GcdStoryType, story_type_row))
    insert(con, 'BondType', rows(GcdSeriesBondType, bond_type_row))
    insert(con, 'Series', rows(GcdSeries, series_row))

    # name details bring the creators they need, as the app's sync does
    name_details = list(rows(GcdCreatorNameDetail, name_detail_row))
    creator_ids = sorted({nd['creator'] for nd in name_details})
    insert(con, 'Creator', rows(GcdCreator, creator_row, GcdCreator.objects.filter(pk__in=creator_ids)))
    have_creators = {r[0] for r in con.execute('SELECT creatorId FROM Creator')}
    insert(con, 'NameDetail', [nd for nd in name_details if nd['creator'] in have_creators])

    have_publishers = {r[0] for r in con.execute('SELECT publisherId FROM Publisher')}
    insert(con, 'Character', [c for c in rows(GcdCharacter, character_row)
                              if c['publisher'] in have_publishers])

    # bonds and the issues they point at (and those issues' variant parents)
    have_series = {r[0] for r in con.execute('SELECT seriesId FROM Series')}
    bonds = [b for b in rows(GcdSeriesBond, series_bond_row)
             if b['origin'] in have_series and b['target'] in have_series]
    wanted = sorted({i for b in bonds for i in (b['originIssue'], b['targetIssue']) if i})
    issues = {}
    for i in range(0, len(wanted), CHUNK):
        for pk, f in serialized(GcdIssue.objects.filter(pk__in=wanted[i:i + CHUNK])):
            issues[pk] = issue_row(pk, f, today)
    parents = sorted({r['variantOf'] for r in issues.values() if r['variantOf']} - set(issues))
    for pk, f in serialized(GcdIssue.objects.filter(pk__in=parents)):
        issues[pk] = issue_row(pk, f, today)
    issues = {k: v for k, v in issues.items() if v['series'] in have_series}
    insert(con, 'Issue', sorted(issues.values(), key=lambda r: r['issueId']))
    have_issues = set(issues)
    insert(con, 'SeriesBond', [b for b in bonds
                               if all(b[k] is None or b[k] in have_issues for k in ('originIssue', 'targetIssue'))])

    con.commit()
    con.execute('PRAGMA foreign_keys=ON')
    bad = con.execute('PRAGMA foreign_key_check').fetchall()
    if bad:
        sys.exit(f'foreign key problems in the seed: {bad[:5]}')
    if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        sys.exit('integrity check failed')

    pages = {
        'publishers': num_pages(GcdPublisher), 'series': num_pages(GcdSeries),
        'name_details': num_pages(GcdCreatorNameDetail), 'characters': num_pages(GcdCharacter),
    }
    identity = con.execute('SELECT identity_hash FROM room_master_table WHERE id=42').fetchone()[0]
    version = con.execute('PRAGMA user_version').fetchone()[0]
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN "
        "('android_metadata','sqlite_sequence','room_master_table')")]
    counts = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    fingerprint = content_hash(con)
    con.execute('VACUUM')
    con.close()
    return identity, version, counts, pages, fingerprint


def write_page_index(directory):
    """The ids the paged-sync endpoints list, so they can answer without asking the database to
    filter and count its tables each time (see db_query/page_index.py)."""
    from db_query import page_index
    from db_query.models import GcdCharacter, GcdCreatorNameDetail, GcdPublisher, GcdSeries
    index = page_index.make({
        'publisher': GcdPublisher, 'series': GcdSeries,
        'name_detail': GcdCreatorNameDetail, 'character': GcdCharacter,
    })
    page_index.write(index, directory)
    return index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'seed'))
    ap.add_argument('--date', default=date.today().isoformat(), help='stamp for lastUpdated and the sync markers')
    a = ap.parse_args()

    django_setup()

    work = tempfile.mkdtemp(prefix='seed_')
    db_path = os.path.join(work, 'issue-database')
    identity, version, counts, pages, fingerprint = build(db_path, a.date)

    index = write_page_index(a.out)

    # sync-progress markers, as the phone would have after a full sync today; the fingerprints say
    # which version of each page it has, so the weekly refresh fetches only pages that changed
    def hashes(name):
        return ','.join(index[name]['hashes'])

    prefs = {
        'updated_publishers': a.date, 'updated_publishers_page': 't' * pages['publishers'],
        'updated_series': a.date, 'updated_series_page': 't' * pages['series'],
        'update_name_details': a.date, 'update_name_details_page': 't' * pages['name_details'],
        'update_characters': a.date, 'update_characters_page': 't' * pages['characters'],
        'update_series_bonds': a.date,
        'updated_publishers_page_hashes': hashes('publisher'),
        'updated_series_page_hashes': hashes('series'),
        'update_name_details_page_hashes': hashes('name_detail'),
        'update_characters_page_hashes': hashes('character'),
    }

    os.makedirs(a.out, exist_ok=True)
    gz_path = os.path.join(a.out, 'seed.db.gz')
    with open(db_path, 'rb') as src, gzip.GzipFile(gz_path, 'wb', compresslevel=9, mtime=0) as dst:
        for chunk in iter(lambda: src.read(1 << 20), b''):
            dst.write(chunk)
    meta = {
        'version': fingerprint, 'builtOn': a.date, 'dbVersion': version,
        'identityHash': identity, 'dbBytes': os.path.getsize(db_path),
        'gzBytes': os.path.getsize(gz_path), 'tables': counts, 'prefs': prefs,
    }
    with open(os.path.join(a.out, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    os.remove(db_path)
    os.rmdir(work)
    print(f"seed {meta['version']}: {meta['dbBytes'] / 1048576:.1f} MB -> {meta['gzBytes'] / 1048576:.1f} MB gz")
    print('rows:', {k: v for k, v in counts.items() if v})


if __name__ == '__main__':
    main()
