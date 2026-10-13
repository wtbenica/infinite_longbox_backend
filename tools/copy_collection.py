#!/usr/bin/env python3
"""Copy My Collection / Wish List items from one copy of the app's database to a phone.

Works one device at a time (no need for both phones connected): pull the source phone's database
to the laptop (adb exec-out run-as ... cat), then merge into the target phone with this tool.
It only adds rows (INSERT OR IGNORE), so it's safe to run again later to pick up new items.

  tools/copy_collection.py --src /path/to/issue-database [--device SERIAL]

Copies: collection items, the issues they point at (plus variant parents), and those issues'
stories, credits and appearances. Series, creators, characters etc. come from the seed.
"""
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

PACKAGE = 'dev.benica.infinite_longbox'


def adb(serial, *args, **kw):
    cmd = ['adb'] + (['-s', serial] if serial else []) + list(args)
    return subprocess.run(cmd, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='source issue-database (with -wal/-shm beside it if any)')
    ap.add_argument('--device', help='target device serial (default: the only connected device)')
    a = ap.parse_args()

    work = tempfile.mkdtemp(prefix='collcopy_')
    src = os.path.join(work, 'src.db')
    tgt = os.path.join(work, 'issue-database')
    shutil.copy(a.src, src)
    for ext in ('-wal', '-shm'):
        if os.path.exists(a.src + ext):
            shutil.copy(a.src + ext, src + ext)

    adb(a.device, 'shell', 'am', 'force-stop', PACKAGE)
    for ext in ('', '-wal', '-shm'):
        with open(tgt + ext, 'wb') as f:
            if adb(a.device, 'exec-out', 'run-as', PACKAGE, 'cat', 'databases/issue-database' + ext,
                   stdout=f).returncode != 0:
                sys.exit('could not read the target database (debug build installed?)')
    backup = tgt + '.backup'
    shutil.copy(tgt, backup)

    con = sqlite3.connect(tgt)
    con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    con.execute(f"ATTACH DATABASE '{src}' AS src")
    ident = lambda db: con.execute(f'SELECT identity_hash FROM {db}.room_master_table WHERE id=42').fetchone()[0]
    if ident('main') != ident('src'):
        sys.exit('schemas differ (different app builds); refusing to merge')

    con.execute('PRAGMA foreign_keys=OFF')
    con.execute('''CREATE TEMP TABLE want_issue AS
        SELECT issue AS issueId FROM src.CollectionItem
        UNION SELECT variantOf FROM src.Issue WHERE variantOf IS NOT NULL
              AND issueId IN (SELECT issue FROM src.CollectionItem)''')
    con.execute('CREATE TEMP TABLE want_story AS SELECT storyId FROM src.Story WHERE issue IN (SELECT issueId FROM want_issue)')
    before = con.execute('SELECT COUNT(*) FROM main.CollectionItem').fetchone()[0]
    for sql in (
        'INSERT OR IGNORE INTO main.UserCollection SELECT * FROM src.UserCollection',
        'INSERT OR IGNORE INTO main.Issue SELECT * FROM src.Issue WHERE issueId IN (SELECT issueId FROM want_issue)',
        'INSERT OR IGNORE INTO main.Story SELECT * FROM src.Story WHERE storyId IN (SELECT storyId FROM want_story)',
        'INSERT OR IGNORE INTO main.Credit SELECT * FROM src.Credit WHERE story IN (SELECT storyId FROM want_story)',
        'INSERT OR IGNORE INTO main.ExCredit SELECT * FROM src.ExCredit WHERE story IN (SELECT storyId FROM want_story)',
        'INSERT OR IGNORE INTO main.Appearance SELECT * FROM src.Appearance WHERE story IN (SELECT storyId FROM want_story)',
        'INSERT OR IGNORE INTO main.CollectionItem SELECT * FROM src.CollectionItem',
    ):
        con.execute(sql)
    con.commit()
    after = con.execute('SELECT COUNT(*) FROM main.CollectionItem').fetchone()[0]

    bad = con.execute('PRAGMA foreign_key_check').fetchall()
    if bad:
        sys.exit(f'foreign key problems after merge, nothing pushed. Backup kept at {backup}: {bad[:5]}')
    con.execute('DETACH DATABASE src')
    con.close()
    for ext in ('-wal', '-shm'):
        if os.path.exists(tgt + ext):
            os.remove(tgt + ext)

    # push back: write through run-as, and drop the stale WAL/SHM on the device
    adb(a.device, 'shell', 'run-as', PACKAGE, 'rm', '-f', 'databases/issue-database-wal', 'databases/issue-database-shm')
    with open(tgt, 'rb') as f:
        r = adb(a.device, 'shell', f'run-as {PACKAGE} sh -c "cat > databases/issue-database"', stdin=f)
    if r.returncode != 0:
        sys.exit(f'push failed; backup at {backup}')
    print(f'collection items on device: {before} -> {after}')
    print(f'backup of the device database before the merge: {backup}')
    adb(a.device, 'shell', 'am', 'start', '-n', f'{PACKAGE}/.MainActivity', stdout=subprocess.DEVNULL)


main()
