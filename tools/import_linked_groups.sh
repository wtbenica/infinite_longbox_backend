#!/bin/bash
# Adds the teams GCD links to stories to the m_character tables of a database.
#   tools/import_linked_groups.sh DATABASE [GCD_DUMP.sql]
# Run it after import_linked_characters.sh. With a dump, the group tables it reads
# (gcd_group_character, gcd_story_character_group; the extractor dropped them) are loaded from it
# first. Connection settings come from the ENV_FILE (default .env.local): HOST, SQL_USER, PASSWORD.
set -euo pipefail
cd "$(dirname "$0")/.."
SCHEMA=${1:?usage: $0 DATABASE [GCD_DUMP.sql]}
DUMP=${2:-}

set -a; . "${ENV_FILE:-.env.local}"; set +a
CNF=$(mktemp); trap 'rm -f "$CNF"' EXIT
printf '[client]\nuser=%s\npassword=%s\nhost=%s\n' "$SQL_USER" "$PASSWORD" "${HOST:-127.0.0.1}" > "$CNF"
SQL() { mariadb --defaults-extra-file="$CNF" "$@"; }

# Loads one table of the dump, replacing the database's; a table runs to the next one's header
load_table() {
    local TABLE=$1
    local START END
    START=$(grep -a -n "^CREATE TABLE \`$TABLE\` " "$DUMP" | head -1 | cut -d: -f1)
    [ -n "$START" ] || { echo "$TABLE not found in $DUMP" >&2; exit 1; }
    END=$(awk -v s="$START" 'NR>s && /^-- Table structure for table/ {print NR; exit}' "$DUMP")
    END=${END:-$(($(wc -l < "$DUMP") + 1))}
    echo "Loading $TABLE from $DUMP (lines $START-$END)"
    { echo "SET FOREIGN_KEY_CHECKS=0; SET UNIQUE_CHECKS=0; SET NAMES utf8mb4;"
      echo "DROP TABLE IF EXISTS $TABLE;"
      echo "/*!40101 SET @saved_cs_client = @@character_set_client */;"
      sed -n "${START},$((END-1))p" "$DUMP"; } | SQL "$SCHEMA"
}

if [ -n "$DUMP" ]; then
    for TABLE in gcd_group_character gcd_story_character_group; do load_table "$TABLE"; done
fi

echo "Merging linked groups into $SCHEMA"
sed "s/{{targetSchema}}/$SCHEMA/g" tools/linked_groups.sql | SQL "$SCHEMA"
SQL "$SCHEMA" -e "select count(*) as linked_teams from m_character where gcd_group_id is not null; select count(*) as linked_team_appearances from m_character_appearance where gcd_group_character_id is not null"
