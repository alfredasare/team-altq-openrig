# Sync v2 runs

How to run sync v2 (`facts_v2`) without duplicating rows or wasting model calls. The code is
`apps/worker/src/cli/sync-v2.ts` and `apps/worker/src/cli/syncV2/`. The rules it follows are in `../rulings.md`.

## The command (from the repo or a worktree root)
```
FACTS_COLLECTION_SUFFIX=_v2 MONGODB_DB=40act_dev bun --env-file=/Users/alfredamoah/AltQ/40act/apps/worker/.env run apps/worker/src/cli/sync-v2.ts --only <cik>[,<cik>…] --out <dir> [flags]
```
- **`FACTS_COLLECTION_SUFFIX=_v2` is required:** the command refuses to start without it, so the canonical `facts`
  is never written. The canonical count is read before and after each fund, and a change fails the run.
- **Which cluster:** the env file decides. The Mac's `apps/worker/.env` is dev; the VM's is prod. Since 2 Nov 2026 the
  command runs on any cluster. Writing prod needs Alfred's yes each time.
- **Indexes:** each run first copies any missing indexes from `facts`, `extraction_runs` and `derive_abstentions`
  onto their `_v2` twins.

## Flags
| Flag | What it does | Model cost |
|---|---|---|
| (none) | Replays: a filing read before under the current prompt version reuses its stored reading; N-PORT/N-CEN filings in the ledger are skipped; equal values are not re-inserted | $0 for funds already read; about $1–2.40 and 8–10 min for a new fund |
| `--steps '<step>,…'` | Only the named steps (e.g. `'offers'`, `'returns table'`, `'statements'`, `'tag keys'`, `'source order'`, `'derive'`), without clearing the fund; removes the re-run reader's older-version rows | $0 if the stored readings match the current prompt version |
| `--reread` (with `--steps`) | Reads the named steps' filings with the model again | **Costs: asks Alfred** |
| `--rebuild` | Clears the fund's v2 rows (keeps readings and copied rows), then replays | $0 for stored readings |
| `--fresh` | Clears everything for the fund, readings included, and reads every filing again | **Costs: asks Alfred** |
| `--concurrency N` | N funds at once in one process, from the de-duplicated `--only` list | none |
| `--resume` (with `--out`) | Skips funds with a result file `<out>/<cik>.json`; a fund with a failed step writes `<cik>.failed.json` instead, so it runs again | none |
| `--report-only` | Writes coverage only, from what `facts_v2` holds | none |

**Check prompt versions before naming a model step.** On 2 Nov 2026 a `--steps` run naming `statements` called the
model for 23 funds ($6.33), because the prompt had moved to `@6` and the stored readings were `@5`. A version bump
means a re-read; say so and the cost before running.

## Rules
- **One run per fund at a time.** Check `ps` before starting; never start a second run on a fund that is running.
- **After a fix,** test it on the one fund it is about. Then re-run only the changed step across the funds
  (`--steps`): about a minute a fund, against 10–17 min for a rebuild. Name `source order` (and `derive`) in
  `--steps` when the re-read reader serves keys in `packages/facts/src/syncV2/sourceOrder.ts`.
- **Before any clearing,** each fund's storage is read. If it can't be read (an expired Google sign-in), the fund
  stops before anything is deleted.
- **A fund's output** is printed as one block; `<out>/<cik>.json` holds the run and the Free-key comparison.
- **Not duplicates:**
  - derive writes a new revision of a series when its explanation changes, even with the same value (e.g. a
    liquidity test whose eligible amount moved);
  - the offer-results step re-adds a few rows each run that source order removes (net zero).

## Alfred's Windows VM (prod batches)
- **Setup:**
  - Git and Bun 1.3.14; the repo on `feature/new-sync`; `bun install --frozen-lockfile`.
  - `apps/worker/.env` with only:
    - `MONGODB_URI` (prod), `MONGODB_DB=40act_dev`, `FACTS_COLLECTION_SUFFIX=_v2`;
    - `GEMINI_API_KEY`;
    - `SEC_STORAGE_BACKEND=gcs`, `SEC_STORAGE_BUCKET`, `GOOGLE_CLOUD_PROJECT`;
    - `GOOGLE_APPLICATION_CREDENTIALS` (a service-account key file, forward slashes);
    - the `AGENTS_*_CONCURRENCY` values;
    - **no `REDIS_URL`**: there is no Redis there.
  - The VM's IP on the prod cluster's Atlas access list.
- **Test first:** run one fund twice. The second run must show `(replayed)` and `$0.000` on every model step.
- **Batch** (PowerShell, from `C:\40act`):
  ```
  $env:CIKS = (Get-Content ciks.txt -Raw).Trim()
  cmd /c "bun --env-file=apps/worker/.env run apps/worker/src/cli/sync-v2.ts --only %CIKS% --concurrency 4 --resume --out runs\v2 >> runs\v2.log 2>&1"
  ```
- **Restart after a stop:** the same two lines. `--resume` skips the finished funds.
- **Watch:**
  - `Get-Content runs\v2.log -Wait -Tail 30`;
  - the count of `runs\v2\*.json` (finished) and `*.failed.json` (to re-run);
  - `Select-String -Path runs\v2.log -Pattern 'failed, nothing more|ERR '`.
- **The 3 Nov 2026 batch:** 263 prod funds (live, with a stored report, without the AIP Alternative Lending Funds
  1709447 and 1709406). No seat runs sync v2 against prod funds until the journal says it finished.
- **Not synced (Alfred, 3 Nov 2026):** the four PIMCO muni funds 1140392, 1170300, 1181504 and 1181506, delisted
  in Aug 2025 and deregistering; listed closed-end funds, not interval or tender offer funds. Take them off any fund
  list a run uses.
- **A storage error on every step** ("norm object missing from storage") has meant the VM's storage settings were
  wrong (the key file path), not missing files.
