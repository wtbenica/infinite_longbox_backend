#!/usr/bin/env python3
"""Compares two starter databases row by row (ignoring the date rows were stamped with).

  tools/compare_seeds.py A.db B.db

Useful for checking tools/build_seed_from_db.py against a seed built from a phone that did a full
sync (tools/build_seed.py): the tables of static data should match apart from what changed in the
backend since. Prints, for each table, how many rows only one has and how many differ, and in which
columns. Pull a phone's database with: adb exec-out run-as dev.benica.infinite_longbox cat
databases/issue-database > A.db (the -wal and -shm files beside it too if there are any).
"""
import sqlite3
import sys

TABLES = {
    'Publisher': 'publisherId', 'Series': 'seriesId', 'Creator': 'creatorId',
    'NameDetail': 'nameDetailId', 'Role': 'roleId', 'StoryType': 'storyTypeId',
    'BondType': 'bondTypeId', 'SeriesBond': 'bondId', 'Issue': 'issueId',
    'Character': 'characterId', 'UserCollection': 'userCollectionId',
}


def rows(con, table, key):
    cols = [r[1] for r in con.execute(f'pragma table_info({table})') if r[1] not in ('lastUpdated', key)]
    data = {r[0]: r[1:] for r in con.execute(f'select {key}, {", ".join(cols)} from {table}')}
    return cols, data


def main(a_path, b_path):
    a, b = sqlite3.connect(a_path), sqlite3.connect(b_path)
    for table, key in TABLES.items():
        cols, x = rows(a, table, key)
        _, y = rows(b, table, key)
        common = x.keys() & y.keys()
        differing = {}
        for i in common:
            for c, p, q in zip(cols, x[i], y[i]):
                if p != q:
                    differing[c] = differing.get(c, 0) + 1
        print(f'{table:15} A {len(x):7}  B {len(y):7}  only A {len(x.keys() - y.keys()):6}  '
              f'only B {len(y.keys() - x.keys()):6}  differing {sum(1 for i in common if x[i] != y[i]):6} {differing or ""}')
    same = lambda con: sorted(r[0] for r in con.execute(
        "select sql from sqlite_master where sql is not null and name not like 'sqlite_%' and name != 'android_metadata'"))
    print('same tables and indexes:', same(a) == same(b))
    print('same Room schema hash:', a.execute('select * from room_master_table').fetchall()
          == b.execute('select * from room_master_table').fetchall())


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
