"""Everything GCD knows about a character, for the app's character page.

The app's characters are rows of m_character: a name, an alter ego and a publisher, linked (when
GCD has a record for it) to a GCD character by gcd_character_id. Records GCD says were republished
as another count as that one, so names, teams and relations are gathered over all of them.
"""
from django.db import connection

REPUBLISHED_AS = 'republished as'

# The story types the app lists: comic stories and covers. An appearance in a promo or an ad
# would lead to an issue where the character is nowhere in the stories the app shows.
STORY_JOIN = ('JOIN gcd_story st ON st.id = a.story_id AND st.deleted = 0 '
              'AND st.type_id IN (6, 19) ')


def _run(sql, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def _marks(items):
    return ','.join(['%s'] * len(items))


def alternate_names(own_name, rows):
    """Names other than [own_name], official ones first, each once whatever its case.

    rows are (name, is_official) pairs.
    """
    seen = {own_name.casefold()}
    names = []
    for name, official in sorted(rows, key=lambda r: (not r[1], r[0].casefold(), r[0])):
        name = name.strip()
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            names.append(name)
    return names


def teams(rows):
    """One entry per team, from (group_id, name, year_joined, year_left, kind, notes) rows.

    A character in a team more than once (two of its records) is listed once, with the earliest
    year joined and the latest year left.
    """
    found = {}
    for group_id, name, joined, left, kind, notes in rows:
        entry = found.setdefault(group_id, {
            'groupId': group_id, 'name': name, 'yearJoined': joined, 'yearLeft': left,
            'membership': kind or '', 'notes': notes or '',
        })
        if joined is not None and (entry['yearJoined'] is None or joined < entry['yearJoined']):
            entry['yearJoined'] = joined
        if left is not None and (entry['yearLeft'] is None or left > entry['yearLeft']):
            entry['yearLeft'] = left
    # two groups with one name are one team to a reader (a reprint, or another universe's copy)
    by_name = {}
    for entry in sorted(found.values(), key=lambda t: (t['yearJoined'] is None, t['yearJoined'] or 0, t['groupId'])):
        by_name.setdefault(entry['name'].casefold(), entry)
    return sorted(by_name.values(), key=lambda t: (t['yearJoined'] is None, t['yearJoined'] or 0, t['name'].casefold()))


def relation_label(kind, reverse_kind, we_are_from):
    """How the other character relates to this one: 'alias of' or the reverse, 'secret identity of'."""
    return kind if we_are_from else (reverse_kind or kind)


def _issue(row):
    if not row:
        return None
    issue_id, series_id, series_name, number, key_date = row
    return {
        'issueId': issue_id, 'seriesId': series_id, 'seriesName': series_name,
        'number': number, 'keyDate': key_date or '',
        'year': int(key_date[:4]) if key_date and key_date[:4].isdigit() else None,
    }


def _first_issue_row(base, where, params, latest=False):
    """The earliest (or [latest]) regular issue with a date, among the rows [base] [where] selects.

    [base] is a FROM clause with the credits or appearances as a, and the story filter on it.
    """
    rows = _run(
        'SELECT a.issue_id, a.series_id, s.name, i.number, i.key_date ' + base +
        'JOIN gcd_issue i ON i.id = a.issue_id AND i.deleted = 0 '
        'JOIN gcd_series s ON s.id = a.series_id ' + where +
        # regular issues before variants, dated before undated, then earliest (or latest)
        ' ORDER BY i.variant_of_id IS NOT NULL, i.key_date IS NULL OR i.key_date = \'\', '
        + ('i.key_date DESC, i.sort_code DESC, i.id DESC' if latest else 'i.key_date, i.sort_code, i.id')
        + ' LIMIT 1', params)
    return rows[0] if rows else None


def _first_issue(character_id, extra=''):
    return _issue(_first_issue_row(
        'FROM m_character_appearance a ' + STORY_JOIN, 'WHERE a.character_id = %s ' + extra, [character_id]))


def _records(gcd_id):
    """The GCD record and every record republished from it, down the chain."""
    ids = {gcd_id}
    frontier = [gcd_id]
    while frontier:
        rows = _run(
            'SELECT r.to_character_id FROM gcd_character_relation r '
            'JOIN gcd_character_relation_type t ON t.id = r.relation_type_id AND t.type = %s '
            'WHERE r.from_character_id IN (' + _marks(frontier) + ')', [REPUBLISHED_AS] + frontier)
        frontier = [r[0] for r in rows if r[0] not in ids]
        ids.update(frontier)
    return sorted(ids)


def one_each(related):
    """GCD often has several records for one identity; list it once, as the one the app has."""
    kept = {}
    for item in related:
        key = (item['relation'], item['name'].casefold(), item['alterEgo'].casefold())
        have = kept.get(key)
        if have is None or (have['characterId'] is None and item['characterId'] is not None):
            kept[key] = item
    return list(kept.values())


def _related(records, own_publisher):
    rows = _run(
        'SELECT r.from_character_id, r.to_character_id, t.type, t.reverse_type '
        'FROM gcd_character_relation r '
        'JOIN gcd_character_relation_type t ON t.id = r.relation_type_id AND t.type <> %s '
        'WHERE r.from_character_id IN (' + _marks(records) + ') '
        'OR r.to_character_id IN (' + _marks(records) + ')',
        [REPUBLISHED_AS] + records + records)
    mine = set(records)
    others = {}
    for from_id, to_id, kind, reverse_kind in rows:
        we_are_from = from_id in mine
        other = to_id if we_are_from else from_id
        if other not in mine:
            others.setdefault(other, relation_label(kind, reverse_kind, we_are_from))
    if not others:
        return []
    ids = sorted(others)
    names = {r[0]: r for r in _run(
        'SELECT id, name, disambiguation FROM gcd_character WHERE deleted = 0 AND id IN ('
        + _marks(ids) + ')', ids)}
    # the app's row for each, the same publisher's first
    app_rows = {}
    for row in _run(
            'SELECT gcd_character_id, id, name, alter_ego, publisher_id FROM m_character '
            'WHERE gcd_character_id IN (' + _marks(ids) + ') ORDER BY publisher_id = %s DESC, id',
            ids + [own_publisher]):
        app_rows.setdefault(row[0], row)
    related = []
    for other in ids:
        if other not in names:
            continue
        _, name, disambiguation = names[other]
        app = app_rows.get(other)
        related.append({
            'relation': others[other],
            'characterId': app[1] if app else None,
            'name': app[2] if app else name,
            'alterEgo': (app[3] if app else None) or '',
            'detail': disambiguation or '',
        })
    return sorted(one_each(related), key=lambda r: (r['relation'], r['name'].casefold()))


def _original_groups(group_ids):
    """Each group's original: a group GCD says was republished as another (a translation, a reprint)
    counts as that one, up the chain."""
    original = {g: g for g in group_ids}
    for _ in range(5):
        pending = sorted({g for g in original.values()})
        rows = _run(
            'SELECT r.to_group_id, r.from_group_id FROM gcd_group_relation r '
            'JOIN gcd_group_relation_type t ON t.id = r.relation_type_id AND t.type = %s '
            'WHERE r.to_group_id IN (' + _marks(pending) + ')', [REPUBLISHED_AS] + pending)
        up = {}
        for copy, source in rows:
            up[copy] = min(source, up.get(copy, source))
        if not up:
            break
        original = {g: up.get(o, o) for g, o in original.items()}
    return original


def _team_rows(records):
    rows = _run(
        'SELECT m.group_id, m.year_joined, m.year_left, t.type, m.notes '
        'FROM gcd_group_membership m '
        'JOIN gcd_group g ON g.id = m.group_id AND g.deleted = 0 '
        'JOIN gcd_group_membership_type t ON t.id = m.membership_type_id '
        'WHERE m.character_id IN (' + _marks(records) + ')', records)
    if not rows:
        return []
    original = _original_groups(sorted({r[0] for r in rows}))
    names = {g: name for g, name in _run(
        'SELECT id, name FROM gcd_group WHERE id IN (' + _marks(sorted(set(original.values()))) + ')',
        sorted(set(original.values())))}
    return [(original[g], names.get(original[g], ''), joined, left, kind, notes)
            for g, joined, left, kind, notes in rows if names.get(original[g])]


def character_info(character_id):
    """The character page's data, or None if the app has no such character."""
    found = _run('SELECT id, name, alter_ego, publisher_id, gcd_character_id FROM m_character WHERE id = %s',
                 [character_id])
    if not found:
        return None
    _, name, alter_ego, publisher_id, gcd_id = found[0]
    publisher = _run('SELECT name FROM gcd_publisher WHERE id = %s', [publisher_id])
    appearances = _run(
        'SELECT COUNT(*), COUNT(DISTINCT a.issue_id) FROM m_character_appearance a ' + STORY_JOIN +
        'WHERE a.character_id = %s',
        [character_id])[0]

    info = {
        'characterId': character_id,
        'name': name,
        'alterEgo': alter_ego or '',
        'publisher': publisher[0][0] if publisher else '',
        'appearances': appearances[0],
        'issues': appearances[1],
        'firstAppearance': _first_issue(character_id),
        'origin': _first_issue(character_id, "AND a.details LIKE '%%origin%%' "),
        'death': _first_issue(character_id, "AND a.details LIKE '%%death%%' "),
        'linked': gcd_id is not None,
        'gcdId': gcd_id,
        'description': '',
        'firstYear': None,
        'alternateNames': [],
        'teams': [],
        'related': [],
    }
    if gcd_id is None:
        return info

    records = _records(gcd_id)
    record = _run('SELECT description, year_first_published FROM gcd_character WHERE id = %s', [gcd_id])
    if record:
        info['description'] = (record[0][0] or '').strip()
        info['firstYear'] = record[0][1]
    info['alternateNames'] = alternate_names(name, _run(
        'SELECT name, is_official_name FROM gcd_character_name_detail '
        'WHERE deleted = 0 AND character_id IN (' + _marks(records) + ')', records) + _run(
        'SELECT name, 0 FROM gcd_character WHERE deleted = 0 AND id IN (' + _marks(records) + ')', records))
    info['teams'] = teams(_team_rows(records))
    info['related'] = _related(records, publisher_id)
    return info
