# 40act platform map

What the team works on, where it lives, and how to tell environments apart. The repo's `CLAUDE.md` is the authority
on code rules; this is the map around it.

## The repo
- **Checkout:** `/Users/alfredamoah/AltQ/40act` (Alfred's: never edit it, use a worktree under
  `/Users/alfredamoah/AltQ/.worktrees/<seat>/`).
- **GitHub:** `git@github.com:94562352QuebecInc/40act.git`.
- **Branches:**
  - `main` is promoted from `development` outside the team;
  - `development` takes PRs;
  - `feature/new-sync` was sync v2's integration branch until 4 Nov 2026, when it merged into `development` (#460).
    Sync v2 work now branches from and targets `development`.
  - Older workstream branches: `feat/tiers`, `feat/aqfid-aqlid`, `feature/aq-report`, `feature/free-version-prep`,
    `feat/nav-nport-quarters` (`history.md`).
- **Bun workspaces monorepo:** TypeScript everywhere, MongoDB. Dependency rule: apps → agents → facts → corpus → db,
  and everyone → contracts.

| Workspace | What it is |
|---|---|
| `packages/contracts` | Every Zod schema (domain, API envelope, agent I/O) and `fixtures/` |
| `packages/db` | Mongo client and repositories; the only place queries live; `src/migrate.ts` applies validators and indexes |
| `packages/corpus` | SEC fetch, object storage (`src/storage/`: keys are frozen), normalization, span retrieval |
| `packages/facts` | Extraction lanes (XBRL, deterministic parsers, model), the metric registry, derive, sync v2's rules (`src/syncV2/`) |
| `packages/agents` | The model client and provider adapters, extract lanes, sync v2 readers and writers (`src/syncV2/`), report pipelines |
| `apps/api` | Hono HTTP API (:3001 in Alfred's dev) |
| `apps/web` | Next.js 16 (:3000 in Alfred's dev); reads the API through `lib/api.ts`/`lib/apiCall.ts`; `API_BASE_URL` points it at an API |
| `apps/worker` | Long-running work (BullMQ, Redis); CLIs in `src/cli/`, sync v2 in `src/cli/sync-v2.ts` and `src/cli/syncV2/` |
| `apps/public-api` | The client API (InvestCloud) |

## Commands (from the repo or a worktree root)
```
bun install                      # root only
bun run dev:web | dev:api | dev:worker
bun run lint                     # the dependency rule; must pass
bun run typecheck                # all workspaces
bun run typecheck:scripts
bun test --path-ignore-patterns='**/*.integration.test.ts'   # what CI runs (~5 min, ~49,700 tests)
bun run --cwd apps/web build     # when apps/web changes
bun run check:nav --expect-host=<cluster>                    # when NAV readers change
```
The web typecheck can fail on stale generated types in `apps/web/.next/` (pages moved under `app/(reader)/`). That
is not the change's fault; say so.

## Databases (MongoDB Atlas)
| Name | Host | Database | Who uses it | How the team reaches it |
|---|---|---|---|---|
| Dev | `ireportauto.ypqtrtp` | `40act_dev` | Alfred, Florian, Nil, the dev deploys | `bin/db.sh dev` (read), `dev-write` (asks) |
| Test | `ireportauto.ypqtrtp` | `40act_test` | Integration tests | `bin/db.sh test`; `MONGODB_DB=40act_test` |
| Prod | `40act.jpjv34a` | **`40act_dev`** (same name!) | The live site | `bin/db.sh prod` (read), `prod-write` (asks) |

- **Tell them apart by HOST,** never by database name. The prod user's name (`m2mireportauto`) contains the dev
  cluster's name, so test the host part only.
- **The addresses** are in `apps/api/.env`: `MONGODB_URI` is dev, `MONGODB_URI_REVIEW` is prod. Only `bin/db.sh`
  reads them, and it never prints them. The prod user has full admin rights, so `bin/db.sh`'s read-only prelude
  is the protection.
- **The dev cluster is small and shared.**
  - About 1 GB of cache, and `40act_dev.facts` has 5.9M documents.
  - Cliffwater 1735964 alone is 1.34M fact rows, and one page load for it read about 2 GB.
  - It also hosts other products' databases.

  Keep sweeps small and sequential, and check `top`/`getLog` before blaming code.
- **Bun reads `.env` from the current folder only.** The root `.env` (gitignored) is for cross-package
  integration tests. `MONGODB_URI is not set` means the wrong folder, not a missing secret.
- **Collections worth knowing:**
  - **Facts:** `facts` (the current flow), `facts_v2` (sync v2), and `facts_legacy` on prod (the old Gemini 3.1 Pro
    extraction, July to 16 Sep 2026).
  - **Sync v2's own:**
    - `extraction_runs_v2`, the ledger: it skips filings already read;
    - `derive_abstentions_v2`;
    - `v2_readings`, the stored model reads, keyed by (cik, accession, group, promptVersion);
    - `v2_source_picks`, the losing readings per key.
  - **Fund metadata:**
    - `funds`, whose `archiveOnly` and `fundType` are `interval_23c3`, `tender_offer_evergreen`, `non_traded_bdc` or
      `unknown`;
    - `filings`, the catalog, with `archive.contentReady` and `archive.files`.
  - **Stored documents** behind the Dashboard and Compare: `sl_peer_funds` (`calendar` = calendar-year returns),
    `sl_return_series`, and the fee schedule.
  - **Admin state:**
    - `tier_fund_scopes`, the per-tier fund lists, which integration tests once wiped on dev;
    - `aq_prompts`, the prompts, edited in admin;
    - `reports`, `score_narrative_edits`.
- **Funds:** dev has 109 funds, 56 live and 53 archive-only. Prod has 330, 329 live, and 265 of those have a stored
  shareholder report. The ~264 in conversation means prod.

## Storage (Google Cloud Storage)
- **Bucket:** `gs://act-498418-sec-raw`, shared by dev and prod.
- **Keys:** `{cik}/{accession}/{name}`; normalized text sits under `{cik}/{accession}/norm/norm-v2/<file>.md`.
  The keys are frozen: changing them needs a bucket migration plan.
- **Reads:** `gcloud storage ls|cat gs://act-498418-sec-raw/<cik>/…`. Writes ask, and deletes are blocked.
- **The Mac's sign-in** is Alfred's gcloud user login and ADC. Both expire (`invalid_grant`, `invalid_rapt`).
  Alfred renews them himself with `gcloud auth login` and `gcloud auth application-default login`.
- **A storage error that reads "norm object missing from storage … storage/catalog drift"** has meant a wrong
  setting, not a missing file:
  - a key file path that doesn't exist (fixed 2 Nov 2026 in `packages/corpus/src/storage/gcs.ts`);
  - a wrong bucket;
  - or local-disk storage.

## SEC
- **EDGAR,** with the User-Agent `AltQ Research aamoah@altq.ai`, under 10 requests a second.
- **The forms that matter:**

| Form | What it holds |
|---|---|
| N-CSR / N-CSRS | Annual and semi-annual shareholder reports: statements, highlights, returns, holdings |
| NPORT-P | Monthly portfolio data, filed quarterly: holdings with asset categories, cash, monthly returns, flows, borrowings (B.2) |
| N-CEN | Annual census: service providers, management fee and net operating expenses (D.8/D.9), one NAV per share |
| N-2 / 486BPOS | Prospectus and its updates: the fee table, objective, classes; often inline XBRL |
| SC TO-I(/A), N-23C3A | Tender offers (tender funds) and repurchase offer notices (interval funds) |
| 10-K / 10-Q | BDCs' reports |
- **What SEC tags,** from a 2026 survey over 330 prod funds:
  - N-CSR XBRL tags only prospectus-style items and NAV;
  - N-PORT XML has anonymous class returns for most funds;
  - N-CEN has one NAV per fund;
  - prospectus iXBRL fee tables cover 81% or more of funds.

## Deploys (Google Cloud Run, project `act-498418`, region `us-east1`)
- **Prod services:** `act-web`, `act-api`, `act-public-api`, `act-worker`.
- **Dev services:** `act-web-dev`, `act-api-dev`, `act-public-api-dev`, `act-worker-dev`.
- **Configs:** `infra/<app>/cloudbuild.yaml` (prod) and `cloudbuild.dev.yaml` (dev). Owners: web and API are
  Nil's, the worker is Alfred's.
- **Before a deploy:** every environment's database must be migrated before a deploy that changes a persisted
  shape (`infra/README.md`). Validators reject documents of the new shape with a bare "Document failed validation".
- **The API's ingress is internal:** Stripe's webhook reaches it through a web route forwarder.

## Models
- **Extraction:** Gemini 3.8 Flash (the `pro` tier resolves to `gemini-3.8-flash` since 14 Sep 2026; Florian chose
  Gemini on 23 Oct).
- **Sync v2's readers:** Gemini 3.8 Flash through Google ADK, with `GEMINI_API_KEY`.
- **The AQ Report:** generation on `modelForReport()`, conform on `gemini-3.6-flash`, research on Perplexity sonar-pro.
- **The prod worker's model env** is checked through `act-worker`'s Cloud Run revision (`AGENTS_MODEL_*`).

## Alfred's Windows VM
Runs long sync v2 batches so his laptop can close (`runbooks/sync-v2.md`). Its `apps/worker/.env` points at prod,
with a Google service-account key and no Redis. The VM's IP must be on the prod cluster's Atlas access list.

## Ports
| Port | Used by |
|---|---|
| 3000, 3001 | Alfred's 40act web and API dev servers: never stop or reuse them |
| 8080, 8081 | Alfred's Gaya dev servers |
| 7433 | OpenRig |
| 7482 | The AltQ Desk |
| 3390–3391 | Gideon's web and API |
| 3490–3491 | Varay's |
| 3590–3591 | Ellie's |
| 3690–3691 | Seris's |

Gaya and 4th-IR use 7480–7481, 3090–3291 and 8090–8291 (`~/Epheotus/machine.md`).
