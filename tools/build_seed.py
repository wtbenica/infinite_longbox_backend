#!/usr/bin/env python3
"""Build the starter-database seed served at /db_query/seed/meta and /db_query/seed/db.

The app's static sync (publishers, series, creators, characters, bonds) takes thousands of paged
requests. A seed is one pre-synced Room database that the app imports on first run, so the paged
sync only has to catch up. The seed is built from a real, fully synced copy of the app's own
database (so it matches the Room schema exactly) with user data and per-item caches stripped.

  tools/build_seed.py                       # pull the DB from the connected phone (debug build)
  tools/build_seed.py --db X --prefs P.xml  # use files you already pulled

Output goes to seed/ (git-ignored): seed.db.gz and meta.json.
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date

PACKAGE = 'dev.benica.infinite_longbox'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'seed')
DUMMY_ID = 2147483647
# Tables that are user data or caches, not part of the shared static data
USER_TABLES = ('Cover', 'CollectionItem')


def adb_pull(rel, dest):
    with open(dest, 'wb') as f:
        r = subprocess.run(['adb', 'exec-out', 'run-as', PACKAGE, 'cat', rel], stdout=f)
    if r.returncode != 0:
        sys.exit(f'could not pull {rel} (is the phone connected with a debug build?)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db')
    ap.add_argument('--prefs')
    a = ap.parse_args()

    work = tempfile.mkdtemp(prefix='seed_')
    db_path = os.path.join(work, 'issue-database')
    prefs_path = os.path.join(work, 'CCPrefs.xml')
    if a.db:
        shutil.copy(a.db, db_path)
        for ext in ('-wal', '-shm'):
            if os.path.exists(a.db + ext):
                shutil.copy(a.db + ext, db_path + ext)
        shutil.copy(a.prefs, prefs_path)
    else:
        subprocess.run(['adb', 'shell', 'am', 'force-stop', PACKAGE])
        for ext in ('', '-wal', '-shm'):
            adb_pull('databases/issue-database' + ext, db_path + ext)
        adb_pull('shared_prefs/CCPrefs.xml', prefs_path)

    con = sqlite3.connect(db_path)
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA wal_checkpoint(TRUNCATE)')

    # strip user data and caches
    for t in USER_TABLES:
        con.execute(f'DELETE FROM {t}')
    # Per-series issues/stories/credits are fetched on demand; only issues referenced by series
    # bonds are part of the static sync. Deleting an issue cascades to its stories, credits, etc.
    con.execute(f'''CREATE TEMP TABLE drop_issue AS SELECT issueId FROM Issue WHERE issueId != {DUMMY_ID}
                    AND issueId NOT IN (SELECT originIssue FROM SeriesBond WHERE originIssue IS NOT NULL
                                        UNION SELECT targetIssue FROM SeriesBond WHERE targetIssue IS NOT NULL)''')
    # Story -> Issue has no cascade, so stories go first (their credits/appearances cascade)
    con.execute('DELETE FROM Story WHERE issue IN (SELECT issueId FROM drop_issue)')
    con.execute('DELETE FROM Issue WHERE issueId IN (SELECT issueId FROM drop_issue)')
    con.commit()

    bad = con.execute('PRAGMA foreign_key_check').fetchall()
    if bad:
        sys.exit(f'foreign key problems in seed: {bad[:5]}')
    if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        sys.exit('integrity check failed')

    identity = con.execute('SELECT identity_hash FROM room_master_table WHERE id=42').fetchone()[0]
    version = con.execute('PRAGMA user_version').fetchone()[0]
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN "
        "('android_metadata','sqlite_sequence','room_master_table')")]
    counts = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    con.execute('VACUUM')
    con.close()
    for ext in ('-wal', '-shm'):
        if os.path.exists(db_path + ext):
            os.remove(db_path + ext)

    # sync-progress markers from the phone's prefs (only the static-sync ones)
    xml = open(prefs_path).read()
    prefs = {n: v for n, v in re.findall(r'<string name="(update[^"]*)">([^<]*)</string>', xml)}

    os.makedirs(OUT, exist_ok=True)
    gz_path = os.path.join(OUT, 'seed.db.gz')
    sha = hashlib.sha256()
    with open(db_path, 'rb') as src, gzip.open(gz_path, 'wb', compresslevel=9) as dst:
        for chunk in iter(lambda: src.read(1 << 20), b''):
            sha.update(chunk)
            dst.write(chunk)
    meta = {
        'version': sha.hexdigest()[:12],
        'builtOn': date.today().isoformat(),
        'dbVersion': version,
        'identityHash': identity,
        'dbBytes': os.path.getsize(db_path),
        'gzBytes': os.path.getsize(gz_path),
        'tables': counts,
        'prefs': prefs,
    }
    with open(os.path.join(OUT, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    shutil.rmtree(work)
    print(f"seed {meta['version']}: {meta['dbBytes']/1048576:.1f} MB -> {meta['gzBytes']/1048576:.1f} MB gz")
    print('rows:', {k: v for k, v in counts.items() if v})
    print('prefs:', {k: (v if len(v) < 12 else f'{len(v)} pages, {v.count("t")} done') for k, v in prefs.items()})


main()
