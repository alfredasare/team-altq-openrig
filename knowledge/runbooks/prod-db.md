# The prod database

Prod is host `40act.jpjv34a`, and its database is **also named `40act_dev`**. The team reaches it only through
`/Users/alfredamoah/AltQ/team-altq/bin/db.sh`.

| Command | What it does | Guard |
|---|---|---|
| `bin/db.sh prod --eval '<js>'` | Read-only: every write method and write command throws before it is sent (`bin/db-readonly.js`) | runs |
| `bin/db.sh prod --file <script.js>` | The same, for a longer read | runs |
| `bin/db.sh prod-write --eval '<js>'` | Writes allowed | **asks Alfred** |

- **The address:** `bin/db.sh` reads it from 40act's `apps/api/.env` (`MONGODB_URI_REVIEW`), checks the host, and
  redacts it from the output. Never read that file or pass a connection string yourself; the guard asks for any
  direct `mongosh`.
- **The prod user has full admin rights.** The read-only protection is the script's (Alfred's choice, 3 Nov 2026),
  so going around it is never acceptable.
- **Never point repo code at prod** (`@40act/db`, scripts): repository helpers create indexes. The exception is a
  sync v2 run Alfred asked for.
- **A prod write needs Alfred's yes for that write.** Write it as one script: what it changes, a count before, the
  write, a count after. Show him the script with the question.
- **Tested on 3 Nov 2026:**
  - a prod `insertOne` was refused before reaching the server;
  - so were writes through `getSiblingDB`, `runCommand({insert})`, an aggregate with `$out`, and a `--file` script;
  - a prod setting pointing at the dev host was refused.
