#!/bin/bash
# Claude Code Notification hook: tell Alfred an agent is waiting (approval prompt or idle question).
input=$(cat)
# Epheotus notifies instead (with a click through to the agent) while it runs with its notifications allowed;
# it keeps this marker only then. Otherwise this hook tells Alfred.
[ -e "$HOME/Library/Application Support/Epheotus/notifying" ] && pgrep -qx Epheotus && exit 0
msg=$(printf '%s' "$input" | /usr/bin/python3 -c 'import json,sys; print(json.load(sys.stdin).get("message","needs your attention"))' 2>/dev/null)
desk=$(basename "${CLAUDE_PROJECT_DIR:-$(pwd)}")
case "$desk" in
  arthur) who="Arthur (AltQ Lead)" ;;  gideon) who="Gideon (AltQ Builder)" ;;  kezess) who="Kezess (AltQ Review)" ;;
  varay) who="Varay (AltQ QA)" ;;      wren) who="Wren (AltQ Challenge)" ;;   ellie) who="Ellie (AltQ Experience)" ;;
  agrona) who="Agrona (AltQ Data)" ;;  tessia) who="Tessia (AltQ Release)" ;; seris) who="Seris (AltQ Security)" ;;
  *) who="AltQ: $desk" ;;
esac
msg=${msg//\"/\'}
/usr/bin/osascript -e "display notification \"${msg:0:180}\" with title \"$who\" sound name \"Glass\"" >/dev/null 2>&1

exit 0
