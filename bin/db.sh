#!/bin/bash
# Mongo shells for the team, without anyone seeing a connection string.
#   db.sh <dev|dev-write|test|prod|prod-write> --eval '<js>'   (or --file <script.js>; --json=relaxed and the like pass through)
#   dev         40act_dev on the dev cluster (shared with Alfred, Florian and Nil), read-only
#   dev-write   the same, writes allowed: the team guard asks Alfred first
#   test        40act_test on the dev cluster, writable (the integration tests' database)
#   prod        40act_dev on the PROD cluster (the same database name on another host), read-only
#   prod-write  the same, writes allowed: the team guard asks Alfred first
# Read-only means db-readonly.js replaces every write method and write command with one that throws before anything is
# sent. The protection is this script's, not the database user's (Alfred chose the existing admin URI, 3 Nov 2026), so
# agents reach prod only through here. The address is read from 40act's apps/api/.env and checked by HOST: the prod
# user's name contains the dev cluster's name, so a test on the whole string would let prod through.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
REPO=/Users/alfredamoah/AltQ/40act
ENVF=${DB_SH_ENV_FILE:-$REPO/apps/api/.env}   # the override exists for this script's own test only
MONGOSH=/opt/homebrew/bin/mongosh

target=${1:-}
[ $# -gt 0 ] && shift
case "$target" in
  dev|dev-write)   var=MONGODB_URI;        host=ireportauto.ypqtrtp; db=40act_dev ;;
  test)            var=MONGODB_URI;        host=ireportauto.ypqtrtp; db=40act_test ;;
  prod|prod-write) var=MONGODB_URI_REVIEW; host=40act.jpjv34a;       db=40act_dev ;;
  *) sed -n '3,8p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac

for a in "$@"; do
  case "$a" in
    mongodb://*|mongodb+srv://*|--host*|--port*|--username*|-u|--password*|-p|--nodb|--authenticationDatabase*)
      echo "db.sh: the connection is this script's; pass only --eval, --file and output options" >&2; exit 2 ;;
  esac
done

uri=$(grep -E "^$var=" "$ENVF" | head -1 | cut -d= -f2- | tr -d '\r"'"'"' ' || true)
[ -n "$uri" ] || { echo "db.sh: $var is not set in $ENVF" >&2; exit 1; }
rest=${uri#*://}; h=${rest##*@}; h=${h%%/*}; h=${h%%\?*}
case "$h" in
  *"$host"*) ;;
  *) echo "db.sh: $var's host is not $host, the cluster '$target' means; stopping" >&2; exit 1 ;;
esac

prelude="db = db.getSiblingDB('$db');"
case "$target" in dev|prod) prelude="$prelude $(cat "$here/db-readonly.js")" ;; esac

set +e
"$MONGOSH" "$uri" --quiet --eval "$prelude" "$@" 2>&1 | sed -E 's#mongodb(\+srv)?://[^ "'"'"']*#<uri>#g'
status=${PIPESTATUS[0]}
exit "$status"
