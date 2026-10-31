#!/bin/bash
# Brings a new GCD dump into the running server without touching the live data until you say so.
#   tools/update_from_dump.sh DUMP.sql[.gz|.zip]   build: load it, run CreditUpdater (--prepare --base the live
#                                                  database, so character ids stay), build the seed; runs in the
#                                                  background and logs to ~/longbox_update/build.log
#   tools/update_from_dump.sh --switch             point the server at what was built, restart it
#   tools/update_from_dump.sh --rollback           put the previous database and seed back
#   tools/update_from_dump.sh --status             what is live, what is built, how the build is going
# Run it on the server. It needs the backend (this repo, with its .venv), CreditUpdater installed with
# `./gradlew installDist` plus its src/main/resources/sql copied beside bin/ (CU_BIN, default ~/CU-dist/bin/CreditUpdater) and the database login in ~/.gcd.cnf.
set -euo pipefail

B=${BACKEND:-$HOME/infinite_longbox_backend}
CU_BIN=${CU_BIN:-$HOME/CU-dist/bin/CreditUpdater}
CNF=${CNF:-$HOME/.gcd.cnf}
STATE=$HOME/longbox_update
SERVICE=${SERVICE:-longbox}
mkdir -p "$STATE"
db() { mariadb --defaults-extra-file="$CNF" "$@"; }
live_name() { sed -n 's/^NAME=//p' "$B/.env"; }
count() { db -N "$1" -e "$2" 2>/dev/null || echo "?"; }
restart() {
    systemctl --user restart "$SERVICE"
    sleep 5
    systemctl --user is-active --quiet "$SERVICE" && curl -sf -m 30 http://127.0.0.1:8000/db_query/seed/meta > /dev/null
}

build() {
    local dump=${1:?usage: $0 DUMP.sql[.gz|.zip]}
    [ -f "$dump" ] || { echo "no such file: $dump"; exit 1; }
    local live new
    live=$(live_name)
    new=gcd_$(date +%Y%m%d_%H%M)
    echo "$(date +%T) live is $live; building $new from $dump"
    db -e "CREATE DATABASE $new CHARACTER SET utf8mb3"
    echo "$(date +%T) loading the dump"
    case $dump in
        *.zip) unzip -p "$dump" ;;
        *.gz) zcat "$dump" ;;
        *) cat "$dump" ;;
    esac | db "$new"
    echo "$(date +%T) running CreditUpdater (a few hours)"
    # CreditUpdater finds its SQL by a path relative to where it runs: src/main/resources/sql next to bin/
    # a new database starts its extraction from the beginning, not where an earlier run left off
    rm -f "$(dirname "$CU_BIN")/../progress.json"
    (cd "$(dirname "$CU_BIN")/.." && "$CU_BIN" --prepare "$new" --base "$live") > "$STATE/creditupdater.log" 2>&1
    grep -q "Successfully updated $new" "$STATE/creditupdater.log" || { echo "CreditUpdater did not finish; see $STATE/creditupdater.log"; exit 1; }
    echo "$(date +%T) building the seed"
    local env seed
    env=$(mktemp "$STATE/env.XXXXXX"); chmod 600 "$env"
    sed "s/^NAME=.*/NAME=$new/" "$B/.env" > "$env"
    seed=$STATE/seed_$new
    ENV_FILE=$env "$B/.venv/bin/python" "$B/tools/build_seed_from_db.py" --out "$seed"
    rm -f "$env"
    printf 'NEW=%s\nSEED=%s\nLIVE_BEFORE=%s\n' "$new" "$seed" "$live" > "$STATE/built"
    echo "$(date +%T) built. $new: $(count "$new" 'SELECT COUNT(*) FROM m_character') characters," \
        "$(count "$new" 'SELECT COUNT(*) FROM m_character_appearance') appearances;" \
        "$live: $(count "$live" 'SELECT COUNT(*) FROM m_character') and $(count "$live" 'SELECT COUNT(*) FROM m_character_appearance')"
    echo "Ready. Run: $0 --switch"
}

switch() {
    [ -f "$STATE/built" ] || { echo "nothing built; run the build first"; exit 1; }
    . "$STATE/built"
    local live
    live=$(live_name)
    [ "$live" != "$NEW" ] || { echo "$NEW is already live"; exit 1; }
    local before after
    before=$(count "$live" 'SELECT COUNT(*) FROM m_character')
    after=$(count "$NEW" 'SELECT COUNT(*) FROM m_character')
    if [ "$before" != "?" ] && [ "$after" != "?" ] && [ $((after * 10)) -lt $((before * 9)) ] && [ -z "${FORCE:-}" ]; then
        echo "$NEW has $after characters against $live's $before; looks wrong. FORCE=1 to switch anyway."
        exit 1
    fi
    cp "$B/.env" "$STATE/env.before"
    [ ! -d "$B/seed" ] || { rm -rf "$B/seed_prev"; mv "$B/seed" "$B/seed_prev"; }
    cp -r "$SEED" "$B/seed"
    sed -i "s/^NAME=.*/NAME=$NEW/" "$B/.env"
    printf 'PREVIOUS=%s\n' "$live" > "$STATE/switched"
    if restart; then
        echo "Switched to $NEW. The server answers; $live and the old seed are kept for --rollback."
    else
        echo "The server did not come back healthy; rolling back"
        rollback
        exit 1
    fi
}

rollback() {
    [ -f "$STATE/env.before" ] || { echo "nothing to roll back"; exit 1; }
    cp "$STATE/env.before" "$B/.env"
    if [ -d "$B/seed_prev" ]; then rm -rf "$B/seed"; mv "$B/seed_prev" "$B/seed"; fi
    restart && echo "Back on $(live_name)." || echo "The server is not healthy; check: systemctl --user status $SERVICE"
}

status() {
    echo "live: $(live_name)"
    [ ! -f "$STATE/built" ] || { . "$STATE/built"; echo "built: $NEW (live before it: $LIVE_BEFORE)"; }
    [ ! -f "$STATE/build.log" ] || { echo "build log:"; tail -5 "$STATE/build.log"; }
    db -N -e "SHOW DATABASES LIKE 'gcd%'" | tr '\n' ' '; echo
}

case ${1:-} in
    --switch) switch ;;
    --rollback) rollback ;;
    --status) status ;;
    -h|--help|"") sed -n '2,10p' "$0" ;;
    *)
        if [ -z "${LONGBOX_BG:-}" ]; then
            LONGBOX_BG=1 nohup "$(readlink -f "$0")" "$@" > "$STATE/build.log" 2>&1 &
            echo "Building in the background; follow it with: tail -f $STATE/build.log (or $0 --status)"
        else
            build "$1"
        fi ;;
esac
