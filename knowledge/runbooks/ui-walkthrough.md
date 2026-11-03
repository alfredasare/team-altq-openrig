# Running the app on a scratch stack, and walking it

Each seat that runs the app has its own ports. Alfred's dev servers on :3000 and :3001 are never stopped or reused.

| Seat | Web | API |
|---|---|---|
| Gideon | 3390 | 3391 |
| Varay | 3490 | 3491 |
| Ellie | 3590 | 3591 |
| Seris | 3690 | 3691 |

## Start (from your worktree or copy, after `bun install`)
- **API:** `PORT=<api port> bun --env-file=/Users/alfredamoah/AltQ/40act/apps/api/.env run --cwd apps/api src/index.ts`
- **Web:** Next reads `.env` files from `apps/web/` in your copy, and a copy has none.
  - Ask Alfred once per copy to link his: `ln -s /Users/alfredamoah/AltQ/40act/apps/web/.env <copy>/apps/web/.env`.
    The guard asks, because it names an env file.
  - Then: `API_BASE_URL=http://localhost:<api port> bun run --cwd apps/web dev --port <web port>`.

These two start commands were written on 3 Nov 2026 and have not been run yet. The first seat to use them fixes this
page if they need changing.
- **Database:** both read the dev database by default. A walk-through never saves anything that changes shared
  state: tier lists, prompts, report edits, fund settings. If a flow can only be tested by saving, stop and ask
  Arthur.
- **Stop** by PID: `lsof -nP -iTCP:<port> -sTCP:LISTEN -t`, check `ps -o command= -p <pid>`, then `kill <pid>`.

## Signing in
- 40act's login is its own page (`/login`), which sends the password through the API to Auth0.
- **Agents never type a password.** When a page needs a signed-in reader, open a headed browser with a profile
  folder under your copy, and ask Arthur to have Alfred sign in. The profile keeps the session for later runs.
- **Staff "Preview as"** shows a page as a Free or Standard reader would see it, once a staff account is signed in.

## Walking with Playwright
- Run Playwright from the copy's `node_modules` (`npx playwright …` or a small script with `node`), headless unless a
  sign-in is needed.
- Full-page screenshots at a wide window (1600 px or more), into `exports/<seat>/<branch>/`.
- Funds worth walking:
  - Hamilton Lane 1803491, with a big highlights history;
  - Apollo Diversified Credit 1676197, with many offers;
  - Xanthus 1076673, a capital-account fund;
  - a Free fund on dev: 1076673, 1609211, 1803491.
- **What to look for** (Ellie's desk has the full list):
  - the numbers carry unit, period and class;
  - blanks stay blank;
  - tier gates hold;
  - no icons;
  - short copy;
  - pages built for many rows.
