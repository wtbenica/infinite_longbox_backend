#!/bin/bash
# Adds GCD's linked story characters to the m_character tables of a database.
#   tools/import_linked_characters.sh DATABASE [GCD_DUMP.sql]
# With a dump, the gcd_story_character table is loaded from it first (the extractor dropped it).
# Connection settings come from the ENV_FILE (default .env.local): HOST, SQL_USER, PASSWORD.
set -euo pipefail
cd "$(dirname "$0")/.."
SCHEMA=${1:?usage: $0 DATABASE [GCD_DUMP.sql]}
DUMP=${2:-}

set -a; . "${ENV_FILE:-.env.local}"; set +a
CNF=$(mktemp); trap 'rm -f "$CNF"' EXIT
printf '[client]\nuser=%s\npassword=%s\nhost=%s\n' "$SQL_USER" "$PASSWORD" "${HOST:-127.0.0.1}" > "$CNF"
SQL() { mariadb --defaults-extra-file="$CNF" "$@"; }

if [ -n "$DUMP" ]; then
    START=$(grep -a -n '^CREATE TABLE `gcd_story_character` ' "$DUMP" | head -1 | cut -d: -f1)
    [ -n "$START" ] || { echo "gcd_story_character not found in $DUMP" >&2; exit 1; }
    # The table runs to the next one's header, or to the end of an excerpt of the dump
    END=$(awk -v s="$START" 'NR>s && /^-- Table structure for table/ {print NR; exit}' "$DUMP")
    END=${END:-$(($(wc -l < "$DUMP") + 1))}
    echo "Loading gcd_story_character from $DUMP (lines $START-$END)"
    { echo "SET FOREIGN_KEY_CHECKS=0; SET UNIQUE_CHECKS=0; SET NAMES utf8mb4;"
      echo "DROP TABLE IF EXISTS gcd_story_character;"
      echo "/*!40101 SET @saved_cs_client = @@character_set_client */;"
      sed -n "${START},$((END-1))p" "$DUMP"; } | SQL "$SCHEMA"
fi

echo "Merging linked characters into $SCHEMA"
sed "s/{{targetSchema}}/$SCHEMA/g" tools/linked_characters.sql | SQL "$SCHEMA"
SQL "$SCHEMA" -e "select count(*) as linked_characters from m_character where gcd_character_id is not null; select count(*) as linked_appearances from m_character_appearance where gcd_story_character_id is not null"
