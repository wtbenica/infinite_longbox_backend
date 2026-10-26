# Tools

How the backend database is built and kept, and the starter database made from it. Everything here is
meant to be run again: the same data gives the same database and the same starter database.

## The pipeline

1. **GCD dump into MariaDB.** CreditUpdater (`--prepare`) shrinks the dump and extracts characters and
   credits. Its steps 5 and 6 are the scripts below, so after a `--prepare` there is nothing else
   to run except the seed. For a database made without those steps, run `refresh_characters_and_seed.sh`.
2. **`linked_characters.sql`** (`import_linked_characters.sh DB [DUMP]`) adds the characters GCD links to
   stories to `m_character` / `m_character_appearance`. It needs the `gcd_story_character` table, which
   CreditUpdater used to drop; pass a dump, or an excerpt of one that has the table, to load it.
3. **`linked_groups.sql`** (`import_linked_groups.sh DB [DUMP]`) does the same for teams: the groups GCD links
   to stories (`gcd_group_character`) and who appeared as part of them (`gcd_story_character_group`, the
   roster). It takes over the extracted characters whose names GCD knows as groups, so a team is a team
   because GCD says so, not because its brackets hold several names.
4. **`merge_duplicate_characters.sql`** (`merge_duplicate_characters.sh DB`) merges characters that are the
   same written differently (same publisher, same name and alter ego or the two swapped, ignoring case,
   spaces and punctuation).
5. **`build_seed_from_db.py`** writes the starter database to `seed/` (`seed.db.gz`, `meta.json`), served
   at `/db_query/seed/meta` and `/db_query/seed/db`. The app downloads it on first run and its sync only
   catches up. It reads the backend database with the models the sync endpoints use and applies the
   conversions the app does; `seed_template.sql` has the tables as the app's Room database makes them.
   When the app's Room schema changes, make the template again from a database the new app created.
   It also writes `page_index.json`: the ids behind the paged-sync endpoints. Counting or paging the
   filtered models (characters, name details) costs 15-30 s per request; with the index they answer in
   about 0.2 s (`db_query/page_index.py`). The index is only used while it still matches the table; if
   the data changes and the index is not rebuilt, the endpoints fall back to the slow way, so run this
   step after any change to the characters or credits.
6. `refresh_characters_and_seed.sh DB [DUMP]` runs 2 to 5.

The scripts that change the database take `ENV_FILE` (default `.env.local`) for the connection.
Merging deletes rows; take a copy of `m_character` and `m_character_appearance` first if you want a way
back (`mariadb-dump --single-transaction DB m_character m_character_appearance`).

## Checking

    ENV_FILE=.env.local python -m unittest discover -s tools/tests -t . -v

* `tools/tests/test_linked_characters.py`, `test_linked_groups.py`, `test_merge_duplicate_characters.py`: run the scripts against a
  small made-up database (`longbox_*_test`, dropped afterwards). Needs the local MariaDB.
* `tools/tests/test_build_seed_from_db.py`: the seed's conversions (dates, issue numbers, barcodes).
* `compare_seeds.py A.db B.db` compares two starter databases row by row, e.g. this one's against one made
  from a phone that did a full sync (`build_seed.py`, which needs a phone).

## Other

* `build_seed.py`: the older way to make the seed, from a synced phone's database.
* `copy_collection.py`: copies My Collection and the Wish List from a pulled copy of the app's database
  to a phone. (The app can now export and import them itself.)
* `cover_list.py`: lists the issues of a series and the cover filename the server expects.
