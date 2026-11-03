#!/bin/bash
# Stop work: the AltQ Desk, the altq team (snapshotted; ./start.sh resumes every conversation) and OpenRig,
# unless another team (Gaya's or 4th-IR's) still runs on it.
# Usage: ./stop.sh [-f]    -f skips the check for agents that are still working
set -u
cd "$(dirname "$0")"
RIG=altq

bin/desk.sh stop >/dev/null

if rig daemon status 2>/dev/null | grep -q running; then
  busy=$(rig ps --nodes --rig "$RIG" --json --filter agentActivity.state=running --fields canonicalSessionName 2>/dev/null \
    | jq -r '[.entries[]?.canonicalSessionName | split("-")[0]] | join(", ")')
  if [ -n "$busy" ] && [ "${1:-}" != "-f" ]; then
    read -r -p "Still working: $busy. Stop anyway? [y/N] " answer
    [[ $answer == [yY]* ]] || { echo "Left everything running (the AltQ Desk too: bin/desk.sh start)."; exit 1; }
  fi
  if rig ps --json | jq -e --arg r "$RIG" '.[] | select(.name == $r and .status == "running")' >/dev/null; then
    rig down "$RIG" --snapshot
  fi
  others=$(rig ps --json | jq -r --arg r "$RIG" '[.[] | select(.name != $r and .status == "running") | .name] | join(", ")')
  if [ -n "$others" ]; then
    echo "OpenRig keeps running for: $others"
  else
    rig daemon stop
  fi
fi
echo "Stopped. ./start.sh brings everything back."
