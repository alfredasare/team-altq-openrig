#!/bin/bash
# Generate each desk's .claude/settings.json from config/base-settings.json + config/roles/<desk>.json, plus the
# `allow` rules of every active project (projects/*/scope.json), and copy into its .claude/rules/ the CLAUDE.md of
# each repo its role lists in "repo_rules", as merged on origin/development (40act's integration branch; main is promoted from it). Run after editing any of them; running seats
# pick changes up on their next launch.
set -euo pipefail
shopt -s nullglob
R="$(cd "$(dirname "$0")/.." && pwd)"
W="$(dirname "$R")"
# Each repo once. Offline, or with a key that wants a passphrase, the last fetched origin/development is used.
for repo in $(jq -r '.repo_rules // [] | .[]' "$R"/config/roles/*.json | sort -u); do
  GIT_SSH_COMMAND='ssh -o BatchMode=yes' git -C "$W/$repo" fetch -q origin development 2>/dev/null \
    || echo "$repo: fetch failed, using the last fetched origin/development"
done
scopes=("$R"/projects/*/scope.json)
projects_allow='[]'
if [ ${#scopes[@]} -gt 0 ]; then
  projects_allow=$(jq -s '[.[] | select(.active) | .allow // []] | add // []' "${scopes[@]}")
  echo "active projects: $(jq -rs '[.[] | select(.active) | .name] | join(", ")' "${scopes[@]}")"
fi
for role in "$R"/config/roles/*.json; do
  desk=$(basename "$role" .json)
  mkdir -p "$R/desks/$desk/.claude"
  # A role with "project_work": false (the reviewer, the browser seat) never gets project write rules.
  jq -s --argjson proj "$projects_allow" '.[0] as $b | .[1] as $r
    | $b
    | .permissions.allow = ($b.permissions.allow + $r.allow + (if $r.project_work == false then [] else $proj end) | unique)
    | .permissions.deny  = (($b.permissions.deny - $r.deny_remove) + $r.deny | unique)' \
    "$R/config/base-settings.json" "$role" > "$R/desks/$desk/.claude/settings.json"
  echo "desks/$desk: $(jq '.permissions.allow|length' "$R/desks/$desk/.claude/settings.json") allow, $(jq '.permissions.deny|length' "$R/desks/$desk/.claude/settings.json") deny"
  # A rules file loads at launch and stays through a compaction, which a CLAUDE.md read by hand doesn't. Copied,
  # since Claude Code doesn't follow a link there; the merged copy, never Alfred's checkout, which may be mid-change.
  mkdir -p "$R/desks/$desk/.claude/rules"
  rm -f "$R/desks/$desk/.claude/rules/repo-"*.md
  for repo in $(jq -r '.repo_rules // [] | .[]' "$role"); do
    sha=$(git -C "$W/$repo" rev-parse --short origin/development)
    # A plain line, since Claude Code hides HTML comments in a rules file.
    { echo "> $repo's CLAUDE.md at origin/development $sha, copied by team-altq/bin/build-desks.sh. Change the repo's file, not this copy."
      git -C "$W/$repo" show origin/development:CLAUDE.md; } > "$R/desks/$desk/.claude/rules/repo-$repo.md"
    echo "desks/$desk: $repo's rules at $sha"
  done
done
