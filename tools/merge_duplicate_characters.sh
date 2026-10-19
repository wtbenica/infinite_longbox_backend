#!/bin/bash
# Merges characters that are the same character written differently (see the .sql for the rules).
#   tools/merge_duplicate_characters.sh DATABASE
# Connection settings come from the ENV_FILE (default .env.local): HOST, SQL_USER, PASSWORD.
set -euo pipefail
cd "$(dirname "$0")/.."
SCHEMA=${1:?usage: $0 DATABASE}

set -a; . "${ENV_FILE:-.env.local}"; set +a
CNF=$(mktemp); trap 'rm -f "$CNF"' EXIT
printf '[client]\nuser=%s\npassword=%s\nhost=%s\n' "$SQL_USER" "$PASSWORD" "${HOST:-127.0.0.1}" > "$CNF"

mariadb --defaults-extra-file="$CNF" "$SCHEMA" -e "select count(*) as characters_before from m_character"
sed "s/{{targetSchema}}/$SCHEMA/g" tools/merge_duplicate_characters.sql | mariadb --defaults-extra-file="$CNF" "$SCHEMA"
mariadb --defaults-extra-file="$CNF" "$SCHEMA" -e "select count(*) as characters_after from m_character"
