#!/bin/bash
# Start work: OpenRig, the altq team (resuming each agent's conversation) and the AltQ Desk.
# Safe to run again: whatever is already up is left alone. The Gaya and 4th-IR teams can run beside it.
set -u
cd "$(dirname "$0")"
RIG=altq

# Agents inherit OpenRig's environment. Keep out an API key (it would bill the API instead of the
# subscription), anything inherited from a Cursor / Claude Code terminal, and 40act settings from Alfred's shell (a
# stray FACTS_COLLECTION_SUFFIX or MONGODB_DB would point an agent's command at the wrong collection or database).
clean=()
for v in $(env | cut -d= -f1 | grep -E '^(ANTHROPIC_API_KEY|GEMINI_API_KEY|OPENAI_API_KEY|CLAUDECODE|CLAUDE_|VSCODE_|GIT_ASKPASS|GIT_EDITOR|TERM_PROGRAM|MONGODB_|FACTS_COLLECTION_SUFFIX)'); do
  clean+=(-u "$v")
done
run() { env ${clean[@]+"${clean[@]}"} "$@"; }

# rig up, minus two notes printed on every restore that need no action.
up() {
  local out status
  out=$(run rig up "$@" 2>&1); status=$?
  printf '%s\n' "$out" | grep -vE 'warning: (FR-5: no durably-bound session name|Restore guidance: .*put back missing blocks)'
  return $status
}

if ! rig daemon status 2>/dev/null | grep -q running; then
  echo "Starting OpenRig…"
  run rig daemon start --no-kernel || exit 1
fi

bin/build-desks.sh >/dev/null || { echo "bin/build-desks.sh failed"; exit 1; }

state=$(rig ps --json | jq -r --arg r "$RIG" '.[] | select(.name == $r) | .status')
case "$state" in
  running) echo "Team $RIG is already running." ;;
  "") echo "Creating team $RIG…"; up rig.yaml ;;
  *) echo "Bringing team $RIG back (takes about a minute)…"; up "$RIG" --existing ;;
esac || echo "Some agents need attention: open their tiles with: rig terminal open $RIG"

# When Epheotus starts the team it is the desk, so the web AltQ Desk is only for starts from the terminal.
if [ -z "${EPHEOTUS:-}" ]; then
  desk_was_up=$(bin/desk.sh status)
  out=$(bin/desk.sh start) || { echo "AltQ Desk: $out"; exit 1; }
  [[ $desk_was_up == running* ]] || open http://localhost:7482
fi

# Remote Control (the Claude app on Alfred's phone) for each seat whose role names a session title
# (config/roles/<name>.json "remote_control"). A resumed seat reconnects by itself (its footer shows /rc); only
# a seat without it gets /remote-control, which on a connected seat opens a menu the agent then waits in.
bottom() { tmux capture-pane -p -t "$1" 2>/dev/null | grep -v '^[[:space:]]*$' | tail -"$2"; }
nodes=$(rig ps --nodes --rig "$RIG" --json 2>/dev/null)
for f in config/roles/*.json; do
  title=$(jq -r '.remote_control // empty' "$f")
  seat=$(jq -r --arg p "$(basename "$f" .json)-" '.[]?.canonicalSessionName // empty | select(startswith($p))' <<<"$nodes")
  [ -n "$title" ] && [ -n "$seat" ] || continue
  for _ in $(seq 24); do # up to two minutes for the agent's prompt to appear
    [[ $(bottom "$seat" 6) == *"❯"* ]] && break
    sleep 5
  done
  sleep 3
  bottom "$seat" 3 | grep -q "/rc" \
    || run rig send "$seat" "/remote-control $title" --raw >/dev/null \
    || echo "Remote Control didn't start for $seat: type /remote-control $title in its tile"
done

echo "AltQ Desk: http://localhost:7482 · terminal tiles: rig terminal open $RIG · stop: ./stop.sh"
