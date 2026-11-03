# How this team works together

- **Durable work is a queue item; a chat message is not work.** When you need a teammate, `rig queue create
  --destination <seat>@altq --summary "…" --body-file <file>` (add `--target-repo 40act`), then
  `rig send <seat>@altq "task <id> is yours"`. Finish with `rig queue handoff` or close it with the result.
  `rig <command> --help` is the current syntax.
- **Say who you are and what you need.** One clear outcome per item, the evidence you already have, the branch
  or worktree, and what "done" looks like.
- **Waiting on Alfred is normal.** When the guard stops a command, tell him in your pane exactly what you want to
  run, against which database or branch, and why. Do not message other seats to run it for you.
- **Don't answer another seat's prompt** or type into its pane. If a teammate is stuck at an approval, tell
  Arthur or Alfred which seat and what it is waiting for.
- **Leave the place better:** when you learn something the next run needs (a quirk, a fixed command, a ruling), add
  it to the right file in `knowledge/` and say so in your report.
