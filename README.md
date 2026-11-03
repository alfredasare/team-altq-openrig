# AltQ 40act team (OpenRig)

Nine Claude Code agents that run on this Mac with Alfred's own `gh`, `gcloud` and git logins, on the 40act repo
(`~/AltQ/40act`). Rig `altq`, spec `rig.yaml`. What each one owns is in `CLAUDE.md`.

| Seat | Agent | Model |
|---|---|---|
| `arthur-lead@altq` | Arthur · Lead (front door, plans, routing, the journal, the final report) | Opus |
| `gideon-build@altq` | Gideon · Builder (code, tests and PRs, in his own worktree; clean-ups) | Opus |
| `kezess-review@altq` | Kezess · Reviewer (correctness and code quality; can't edit or push) | Opus |
| `varay-qa@altq` | Varay · QA (the gates, `40act_test` integration runs, reproductions) | Opus |
| `wren-challenge@altq` | Wren · Challenger (challenges every real plan before it reaches Alfred; can't edit or push) | Opus |
| `ellie-ux@altq` | Ellie · Experience (walks every UI change with Playwright on her own ports; can't edit the repo) | Opus |
| `agrona-data@altq` | Agrona · Data (values against the filings; dev and prod reads; can't edit code) | Opus |
| `tessia-ops@altq` | Tessia · Release & Ops (Google Cloud and infra, CI, releases, migrations; changes on Alfred's yes; sync v2 batches) | Opus |
| `seris-security@altq` | Seris · Security (auth, tiers, partner scoping and billing on scratch copies) | Opus |

## Start and stop
```
~/AltQ/team-altq/start.sh     # OpenRig + the team (conversations resumed) + the AltQ Desk, opened in the browser
~/AltQ/team-altq/stop.sh      # the AltQ Desk + the team (snapshotted); OpenRig too unless another team runs
```
- **Safe to run twice:** both scripts leave whatever is already up or down alone. Gaya, 4th-IR and AltQ share one
  OpenRig and run side by side.
- **First launch:** on a brand-new rig, each agent asks once whether to trust its desk folder ("No" is preselected).
  Pick "Yes, I trust this folder", then run `rig seat continue <seat>@altq`.
- **Terminal tiles:** `rig terminal open altq` shows the agents' terminals.

## Epheotus
Add the workspace from the app's Add form:

| Field | Value |
|---|---|
| Name | AltQ |
| Folder | `~/AltQ/team-altq` |
| Rig | `altq` |
| Avatars | `avatars` |
| Journal | `knowledge/journal` |
| Exports | `exports` |
| Checks | `gh auth status` and `gcloud auth list` |

The portraits are `avatars/<pod>.webp`.

## AltQ Desk (web UI)
**http://localhost:7482**, started and stopped by the scripts above (on its own: `bin/desk.sh start|stop|status`;
log in `.run/altq-desk.log`).
- It is the 4th-IR team's Ops Desk (`~/4th-IR/devops-openrig/ui`), run with `OPS_DESK_RIG=altq`.
- Its portraits come from that UI's own folder, which has Arthur, Gideon, Kezess, Varay, Tessia and Seris. Ellie,
  Wren and Agrona show their initial there, as on the Gaya Desk. Epheotus shows all nine.

## From your phone (Remote Control)
Each seat whose role file names a session (`"remote_control": "altq · Arthur"` in `config/roles/<name>.json`) shows up
under that name in the Claude app and at claude.ai/code. `start.sh` connects any that aren't.

## Working with the team
- **Requests:** anything with more than one step goes to Arthur (his chat in Epheotus or the desk, or
  `rig send arthur-lead@altq "…"`). A value question can go straight to Agrona.
- **Approvals:** a gated command stops in the agent's tile with a `Team guard: …` reason. The tiers are in
  `knowledge/approvals.md`.
- **Databases:** agents reach Mongo only through `bin/db.sh <dev|test|prod>`. Dev and prod are read-only there;
  `dev-write` and `prod-write` ask you (`knowledge/runbooks/prod-db.md`).
- **Memory:** `knowledge/`, which opens as an Obsidian vault.
  - `journal/`: Arthur's daily record;
  - `history.md`, `rulings.md`, `platform-map.md`, `people.md`, `artifacts.md`, `backlog.md`;
  - `runbooks/`.

## Changing the setup
| Change | Edit | Takes effect |
|---|---|---|
| Commands that run without asking / never run | `config/base-settings.json`, `config/roles/<desk>.json` | after `bin/build-desks.sh` (start.sh runs it), at the seat's next launch |
| Gated / blocked commands | `hooks/guard.py` (add a case to `CASES`) | immediately; check with `hooks/guard.py --selftest` |
| Persona, duties, team rules | `desks/<name>/CLAUDE.md`, `CLAUDE.md`, `CULTURE.md` | at the seat's next launch |
| 40act's rules a seat loads at launch | copied from `origin/development` by `bin/build-desks.sh` | after it runs, at the seat's next launch |
| Facts, rulings, runbooks, backlog | `knowledge/` | when an agent next reads it |
| A new seat | `rig.yaml`, `agents/team/agent.yaml`, its desk and role files | `rig spec validate rig.yaml`, `bin/build-desks.sh`, then `rig expand` with the team running (the Gaya team's README has the steps) |
