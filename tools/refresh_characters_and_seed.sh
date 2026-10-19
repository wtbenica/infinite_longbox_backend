#!/bin/bash
# Everything after the GCD data is in the database, in one go: the characters GCD links to stories,
# merging characters that are the same, and the starter database the app downloads on first run.
#   tools/refresh_characters_and_seed.sh DATABASE [GCD_DUMP_OR_EXCERPT.sql]
# Safe to run again, and the same data gives the same database and the same seed. With a dump (or
# an excerpt of it with the gcd_story_character table) the link table is loaded from it first.
# Connection settings come from ENV_FILE (default .env.local); the python is the one running this
# (activate the venv first), or PYTHON=...
set -euo pipefail
cd "$(dirname "$0")/.."
SCHEMA=${1:?usage: $0 DATABASE [GCD_DUMP.sql]}
DUMP=${2:-}

tools/import_linked_characters.sh "$SCHEMA" ${DUMP:+"$DUMP"}
tools/merge_duplicate_characters.sh "$SCHEMA"
"${PYTHON:-python}" tools/build_seed_from_db.py
