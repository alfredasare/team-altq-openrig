#!/bin/bash
# Run the AltQ Desk in the background on http://localhost:7482: the 4th-IR team's Ops Desk UI
# (~/4th-IR/devops-openrig/ui) pointed at the altq rig, with this folder's inbox and exports.
# Usage: desk.sh <start|stop|status>
set -u
dir="$(cd "$(dirname "$0")/.." && pwd)"; run="$dir/.run"; pidf="$run/altq-desk.pid"; mkdir -p "$run"
ui=/Users/alfredamoah/4th-IR/devops-openrig/ui; port=7482; url="http://localhost:$port"
alive() { [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; }
case "${1:-status}" in
  start)
    alive && { echo "running: $url"; exit 0; }
    holder=$(lsof -nP -iTCP:$port -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $1" (pid "$2")"}')
    [ -z "$holder" ] || { echo "port $port is taken by $holder"; exit 1; }
    [ -d "$ui/node_modules" ] || (cd "$ui" && npm install --no-fund --no-audit) || exit 1
    [ -d "$ui/dist" ] || (cd "$ui" && npm run build >/dev/null) || { echo "build failed: cd $ui && npm run build"; exit 1; }
    cd "$ui" || exit 1
    OPS_DESK_RIG=altq OPS_DESK_PORT=$port OPS_DESK_TITLE="AltQ Desk" OPS_DESK_HOME="$dir" \
      nohup node server/main.ts >"$run/altq-desk.log" 2>&1 </dev/null &   # node itself, so the pid file is its pid
    echo $! >"$pidf"
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      sleep 1
      alive || break
      curl -sf -o /dev/null "$url/api/state" && { echo "$url"; exit 0; }
    done
    echo "failed to start:"; tail -5 "$run/altq-desk.log"; exit 1 ;;
  stop) alive && kill "$(cat "$pidf")" && echo "stopped"; rm -f "$pidf" ;;
  status) alive && echo "running: $url" || echo "not running" ;;
  *) echo "usage: $0 <start|stop|status>"; exit 1 ;;
esac
