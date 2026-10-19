"""Everything GCD knows about a creator, for the app's creator page.

The app's creators are GCD's own (gcd_creator), so ids are the same. The tables GCD keeps about a
creator's schools, awards and relatives are not in our database; what is here is the record
itself (bio, birth and death), the other names they have worked under, and their credits.
"""
import re

from db_query.character_info import STORY_JOIN, _first_issue_row, _issue, _marks, _run

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# credit type names are lists of these ("pencils and inks"); each is a role of its own to a reader
ROLES = [('script', 'Writer'), ('pencils', 'Penciler'), ('inks', 'Inker'), ('colors', 'Colorist'),
         ('letters', 'Letterer'), ('painting', 'Painter'), ('editing', 'Editor')]

NAME_KINDS = {
    'Pen Name': 'pen name', 'Name at Birth': 'birth name', 'Changed Name': 'changed name',
    'House Name': 'house name', 'Studio Name': 'studio', 'Ghost Name': 'ghost name',
    'Joint Name': 'joint name', 'Common Alternative Name': '',
}


def date_text(year, month, day):
    """'Aug 28, 1917', 'Aug 1917' or '1917'; blank if there is no year (GCD uses '' and '0')."""
    year = (year or '').strip()
    if not year.isdigit() or int(year) == 0:
        return ''
    month = int(month) if (month or '').isdigit() and 1 <= int(month) <= 12 else None
    day = int(day) if (day or '').isdigit() and 1 <= int(day) <= 31 else None
    if month is None:
        return year
    return f'{MONTHS[month - 1]} {day}, {year}' if day else f'{MONTHS[month - 1]} {year}'


def place_text(*parts):
    """'Thousand Oaks, California, United States': the parts that are there, in order, once each."""
    seen, out = set(), []
    for part in parts:
        part = (part or '').strip()
        if part and part.casefold() not in seen:
            seen.add(part.casefold())
            out.append(part)
    return ', '.join(out)


def role_counts(rows):
    """[{'role', 'count'}] biggest first, from (credit_type_name, credits) rows.

    A credit as 'pencils and inks' counts toward both Penciler and Inker.
    """
    totals = {}
    for type_name, count in rows:
        words = (type_name or '').lower()
        for word, role in ROLES:
            if word in words:
                totals[role] = totals.get(role, 0) + count
    order = [role for _, role in ROLES]
    return [{'role': role, 'count': n}
            for role, n in sorted(totals.items(), key=lambda kv: (-kv[1], order.index(kv[0])))]


def other_names(own_name, rows):
    """[{'name', 'kind'}]: rows are (name, is_official, type_name). Misspellings are left out."""
    seen = {own_name.casefold()}
    names = []
    for name, official, type_name in sorted(rows, key=lambda r: (not r[1], r[0].casefold(), r[0])):
        name = name.strip()
        if not name or name.casefold() in seen or type_name == 'Misspelled Name':
            continue
        seen.add(name.casefold())
        names.append({'name': name, 'kind': NAME_KINDS.get(type_name, '')})
    return names


LINK = re.compile(r'\[gcd_link_(\w+)\]\((\d+)\)')


def link_ids(text):
    """{kind: {ids}} of the GCD links in a bio, which writes 'Jack Kirby' as [gcd_link_creator](2)."""
    found = {}
    for kind, ident in LINK.findall(text or ''):
        found.setdefault(kind, set()).add(int(ident))
    return found


def resolve_links(text, names):
    """The bio with each link replaced by the name [names] has for (kind, id).

    A link to something we have no name for (GCD's features, which are not in our database) is
    dropped, and the gaps it leaves are closed up.
    """
    text = LINK.sub(lambda m: names.get((m.group(1), int(m.group(2))), ''), text or '')
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    text = re.sub(r',(\s*,)+', ',', text)
    return re.sub(r'[ \t]{2,}', ' ', text).strip()


NAME_SQL = {
    'creator': 'SELECT id, gcd_official_name FROM gcd_creator WHERE id IN ({})',
    'publisher': 'SELECT id, name FROM gcd_publisher WHERE id IN ({})',
    'series': 'SELECT id, name FROM gcd_series WHERE id IN ({})',
    'character': 'SELECT id, name FROM gcd_character WHERE id IN ({})',
}


def _link_names(text):
    names = {}
    for kind, ids in link_ids(text).items():
        sql = NAME_SQL.get(kind)
        if sql and ids:
            ids = sorted(ids)
            for ident, name in _run(sql.format(_marks(ids)), ids):
                names[(kind, ident)] = name
    return names


def _credit_source(details):
    """The credits of these name details as a derived table [a], and the parameters it takes.

    Credits are in two tables: GCD's own linked records (gcd_story_credit) and the ones
    CreditUpdater extracted from the stories' text (m_story_credit). UNION counts a credit that is
    in both once.
    """
    one = ('SELECT creator_id, credit_type_id, story_id, issue_id, series_id FROM {} '
           'WHERE deleted = 0 AND creator_id IN (' + _marks(details) + ')')
    return ('(' + one.format('gcd_story_credit') + ' UNION ' + one.format('m_story_credit') + ') a ',
            list(details) + list(details))


def creator_info(creator_id):
    """The creator page's data, or None if there is no such creator."""
    found = _run(
        'SELECT c.id, c.gcd_official_name, c.disambiguation, c.bio, '
        'bd.year, bd.month, bd.day, c.birth_city, c.birth_province, bc.name, '
        'dd.year, dd.month, dd.day, c.death_city, c.death_province, dc.name '
        'FROM gcd_creator c '
        'LEFT JOIN stddata_date bd ON bd.id = c.birth_date_id '
        'LEFT JOIN stddata_country bc ON bc.id = c.birth_country_id '
        'LEFT JOIN stddata_date dd ON dd.id = c.death_date_id '
        'LEFT JOIN stddata_country dc ON dc.id = c.death_country_id '
        'WHERE c.id = %s AND c.deleted = 0', [creator_id])
    if not found:
        return None
    (_, name, disambiguation, bio, by, bm, bday, bcity, bprov, bcountry,
     dy, dm, dday, dcity, dprov, dcountry) = found[0]

    details = [r[0] for r in _run(
        'SELECT id FROM gcd_creator_name_detail WHERE creator_id = %s AND deleted = 0', [creator_id])]

    info = {
        'creatorId': creator_id,
        'name': name,
        'disambiguation': disambiguation or '',
        'born': {'date': date_text(by, bm, bday), 'place': place_text(bcity, bprov, bcountry)},
        'died': {'date': date_text(dy, dm, dday), 'place': place_text(dcity, dprov, dcountry)},
        'bio': resolve_links(bio, _link_names(bio)),
        'otherNames': other_names(name, _run(
            'SELECT d.name, d.is_official_name, t.type FROM gcd_creator_name_detail d '
            'LEFT JOIN gcd_name_type t ON t.id = d.type_id '
            'WHERE d.creator_id = %s AND d.deleted = 0', [creator_id])),
        'credits': 0, 'issues': 0, 'roles': [], 'firstCredit': None, 'latestCredit': None,
        'topSeries': [],
    }
    if not details:
        return info

    # GCD's own credit records and the ones extracted from the stories' text, each counted once
    source, params = _credit_source(details)
    base = 'FROM ' + source + STORY_JOIN
    totals = _run('SELECT COUNT(*), COUNT(DISTINCT a.issue_id) ' + base, params)[0]
    info['credits'], info['issues'] = totals[0], totals[1]
    if not info['credits']:
        return info

    info['roles'] = role_counts(_run(
        'SELECT t.name, COUNT(*) ' + base + 'JOIN gcd_credit_type t ON t.id = a.credit_type_id '
        'GROUP BY t.name', params))
    info['firstCredit'] = _issue(_first_issue_row(base, '', params))
    info['latestCredit'] = _issue(_first_issue_row(base, '', params, latest=True))
    info['topSeries'] = [
        {'seriesId': sid, 'seriesName': sname, 'issues': n}
        for sid, sname, n in _run(
            'SELECT a.series_id, s.name, COUNT(DISTINCT a.issue_id) AS n ' + base +
            'JOIN gcd_series s ON s.id = a.series_id '
            'GROUP BY a.series_id, s.name ORDER BY n DESC, s.name LIMIT 8', params)]
    return info
