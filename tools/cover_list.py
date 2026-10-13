#!/usr/bin/env python3
"""List the issues of a series and the cover filename the local server expects.

  tools/cover_list.py "amazing spider-man"          # find series by name
  tools/cover_list.py --series 12345                # list a series' issues
  tools/cover_list.py --series 12345 --missing      # only issues without a cover in covers/

Covers go in covers/<issue id>.jpg (png/webp/gif also work).
"""
import argparse
import os
import subprocess
import sys

SOCKET = os.path.expanduser('~/mariadb-gcd/mariadb.sock')
COVERS = os.path.join(os.path.dirname(__file__), '..', 'covers')


def query(sql):
    out = subprocess.run(
        ['mariadb', '--no-defaults', '-S', SOCKET, '-ugcd', '-pgcd', 'gcd', '-N', '-B', '-e', sql],
        capture_output=True, text=True, check=True).stdout
    return [line.split('\t') for line in out.splitlines()]


def has_cover(issue_id):
    return any(os.path.isfile(os.path.join(COVERS, f'{issue_id}.{e}'))
               for e in ('jpg', 'jpeg', 'png', 'webp', 'gif'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name', nargs='?')
    ap.add_argument('--series', type=int)
    ap.add_argument('--missing', action='store_true')
    a = ap.parse_args()
    if a.series:
        rows = query(f"select id, number, ifnull(variant_of_id,''), publication_date from gcd_issue "
                     f"where series_id={a.series} order by sort_code")
        for i, num, variant, date in rows:
            if a.missing and has_cover(i):
                continue
            tag = f'  (variant of {variant})' if variant else ''
            print(f'{i}.jpg\t#{num}\t{date}{tag}{"" if not has_cover(i) else "  [have]"}')
    elif a.name:
        like = a.name.replace("'", "''")
        for r in query(f"select s.id, s.name, s.year_began, p.name, s.issue_count from gcd_series s "
                       f"join gcd_publisher p on p.id=s.publisher_id where s.name like '%{like}%' "
                       f"order by s.issue_count desc limit 40"):
            print(f'series {r[0]}\t{r[1]} ({r[2]})\t{r[3]}\t{r[4]} issues')
    else:
        ap.print_help(); sys.exit(1)


main()
