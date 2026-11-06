# Adding a key to sync v2

How a key is added, proven and locked, for the Professional work (`../professional.md`). Anchors are on
`origin/development` at `3ab14a779` (6 Nov 2026): check them again before relying on a line number. Running sync v2:
`sync-v2.md`.

## The loop (Alfred, 6 Nov 2026)
One set of keys at a time, simple parser keys first.
1. **Find the value first** (Agrona). Open the filing the list names, then the others: the named document may not
   hold it. Record the form, the item or section, and two or three funds where it prints.
2. **Register and build it** (Gideon): the steps for its kind, below.
3. **One fund:** run the step on dev for a fund where the value prints. Read what was written (below) and compare it
   with the filing.
4. **A few more funds,** chosen to differ: interval and tender-offer, a fund where the value is absent, a
   multi-class fund for a class key. Fix and re-run until every one is right.
5. **The dev test funds** (the 27 in `../professional.md`). Agrona checks the values against the filings, quoting
   the line and linking the filing.
6. **Lock the set:** tests and gates green, the PR opened, Alfred merges. Then the next set.

Correct values come first: no cost approval is needed for these runs on dev (Alfred, 6 Nov). Keep `--only` to the
funds in the current test. The guard still asks for `--fresh` and `--reread`; a prompt version bump re-reads without
them. Prod runs ask Alfred.

## Every key: register it
- **Definition** (`packages/facts/src/registry/types.ts:86-156`): key, label, definition, unit, normalization,
  axis (from `axes.ts`, e.g. `share_class`), producer, families, sections, lanes, derivation, `legacy: []`, status.
- **What `registry.test.ts` enforces:** a `pct` key's normalization says "percent points"; a `usd` key's says
  "whole dollars"; a date is unit `text`; the axis exists. The label must be unique among active keys
  (`scripts/lib/keyGuardrails/registryGuardrails.test.ts`).
- **The pinned count:** `packages/facts/src/registry/reconcile.test.ts:118` (519 on 6 Nov). Bump it and extend the
  comment's sum.
- **A `share_class` key** goes into `scripts/lib/shareClassKeys/keyCatalog.ts` (a family, or
  `EXCLUDED_SHARE_CLASS_KEYS` with a reason); `keyCatalog.test.ts` fails otherwise. It was forgotten twice
  (`66427e439`, `7ef43207d`).
- **A key a v1 model reader also produces:** its definition and normalization go into v1's prompt too. Wording only
  sync v2 needs goes in the v2 reader's guidance (`1e2996bd3` used `FALLBACK_GUIDANCE`).

## 1. A key parsed from N-CEN or N-PORT tags
Examples: `5d6df1b59`, `ae7871e21`.
1. **Register** in `registry/metrics/filingsStructuredNcen.ts` or `filingsStructuredNport.ts`: producer
   `filings_structured`, lanes `['deterministic']`, named after the tag in snake_case (`../rulings.md`).
2. **Parse** in `packages/facts/src/syncV2/tagKeys.ts`. Add the key to `NCEN_TAG_METRICS` or `NPORT_TAG_METRICS`,
   then read it in `ncenTagValues` (series-scoped, through `parseNcen`), `singleSeriesTags` (single-series N-CENs
   only) or `nportTagValues`.
3. **Version:** bump `TAG_KEYS_EXTRACTOR` (`packages/agents/src/syncV2/tagKeysWriter.ts:19`, `syncv2-tag-keys@2`)
   when existing output changes or a key goes. There is no ledger: each run reads the filings again and deletes older
   versions' rows first.
4. **Static key** (one value per fund or class, from the newest N-CEN): add a `SOURCE_ORDER` ncen entry and a
   `STATIC_KEYS` entry (`sourceOrder.ts`), and add it to the list in `sourcePick.test.ts`. A dynamic key needs no
   entry (`management_fee` has none).
5. **Tests:** `tagKeys.test.ts` (parsing); `tagKeysWriter.integration.test.ts` on `40act_test` (the key set, no
   duplicates on a second run, the old-version purge).
6. **Run:** `--steps 'tag keys,source order'`.

Not the N-CEN governance lane (`governance/parseNcen.ts`, `ncenBoard.ts`, `agents/src/extract/ncenFacts.ts`): it is
v1's lane, shared with sync v2's `ncen` step, keeps a ledger, and its changes were re-read with `--reread`. Put a
v2-only key in `tagKeys.ts`. `board_member_affiliation` comes from that lane.

## 2. A key the model reads from the prospectus (fallback)
Example: `1e2996bd3` (`repurchase_cap_pct`).
1. **Register:** its definition and normalization become the prompt line (`fallbackReader.ts:40-48`).
2. **Rules** in `packages/facts/src/syncV2/fallback.ts`: its parse and axis in `RULES`; optional
   `FALLBACK_GUIDANCE`.
3. **Source order is required:** a `SOURCE_ORDER` step with family `prospectus`, or the key is never asked. Add
   `STATIC_KEYS` if the value doesn't change between filings.
4. **Version:** `FALLBACK_PROMPT_VERSION` (`fallbackReader.ts:15`, `syncv2-fallback@4`). A new key needs no bump: a
   stored reading is reused only if it asked for every missing key, so the next run reads the whole prospectus again
   ($0.22–0.51 a fund).
5. **Tests:** `fallback.test.ts`, `fallbackReader.test.ts`, `sourcePick.test.ts`.
6. **Run:** `--steps 'fallback,source order'`.

A key read from one tagged prospectus section (`cef:CapitalStockTableTextBlock` and the like, "scoped" on Nil's
page) is new code: no step reads a tagged text block today. Plan it with Arthur before building.

## 3. A key read from the shareholder report (statements, highlights, notes)
Example: `79e988c1d` added `net_capital_transactions`; `b8ce55726` and `e7fc02e6a` changed its rules.
- **The reading already has the rows** (as `79e988c1d` used the existing `capital_*` roles): code only, in
  `statementValues.ts` (`STATEMENT_METRICS`, `pick`), `highlights.ts` or `noteValues.ts` (`NOTE_METRICS`). Stored
  readings are served again with no model call.
- **It needs a new role or field:**
  1. contracts first (`packages/contracts/src/syncV2.ts`: highlights roles, statement roles, notes output), in their
     own commit with fixtures;
  2. the prompt (`statementsPrompt.ts`, `highlightsPrompt.ts`, `notesPrompt.ts` in `packages/agents/src/syncV2/`);
  3. bump its version: `syncv2-statements@6`, `syncv2-highlights@5`, `syncv2-notes@9`. Readings are matched by
     version, so each fund's next run reads its reports again. The old reading stays in `v2_readings`. Older-version
     facts are deleted only by `--steps <reader>` or `--rebuild`/`--fresh`, so re-run with `--steps`.
- **Source order:** add a `SOURCE_ORDER` entry; keys outside it are left alone.
- **If derive also writes the key,** add it to derive's skip list (`runFund.ts`).
- **Tests:** `statements.test.ts`, `statementsReader.test.ts` (pins the draft count), the highlights and notes tests.
- **Run:** `--steps 'statements,source order'` (or `highlights`, or `offer results in reports` for the notes).

The highlights reading already asks for each class's `net_assets_end`, and nothing serves it yet
(`highlightsPrompt.ts:47`).

## 4. A computed key
- **Formula key (sync v2 only):**
  1. register in `filingsStructuredNport.ts` with lanes `['deterministic']` and no derivation (a `derived` lane
     claims a deriver that doesn't exist: `66427e439`);
  2. the function in `formulaKeys/nportFigures.ts` or `ncenFigures.ts`; the key in `FORMULA_METRICS`, its inputs in
     `FORMULA_INPUT_METRICS`, called from `formulaKeyValues` (`formulaKeys/index.ts`);
  3. bump `FORMULA_KEYS_EXTRACTOR` (`formulaKeysWriter.ts:18`, `syncv2-formula-keys@6`); the writer deletes other
     versions' rows on every run. No source order entry.
  4. tests: `formulaKeys.test.ts`, `formulaKeysWriter.integration.test.ts`; run `--steps 'formula keys'`.
- **Derive** (shared with v1; only when v1 needs the key too): lanes `derived` with a derivation, a function in
  `DERIVERS` (`derive/index.ts`), `DERIVE_VERSION` `derive@25`. The `derive` step takes 10–17 minutes a fund.

## Removing or renaming a key
- `RETIRED_KEYS` and its writer prefix in `RETIRED_KEY_WRITERS` (`retiredKeys.ts`): the source order step deletes
  the rows. Prospectus keys: `RETIRED_FALLBACK_KEYS` (`fallback.ts`), deleted by the fallback step.
- Take it out of `SOURCE_ORDER`, `STATIC_KEYS`, the `sourcePick.test.ts` list, the registry (and the count), and the
  key catalog.
- A rename has been done as a new key plus the old one retired (`share_class_ticker` to
  `common_stock_ticker_symbol`, 3 Nov). `CANONICAL_NAMES` (`canonicalNames.ts`) holds Florian's names, applied only
  with `--canonical-names`.

## Steps and reading what a run wrote
- `--steps` names match by prefix (`runFund.ts`): `nport`, `ncen`, `prospectus fee table`, `tag keys`,
  `deregistration`, `highlights`, `statements`, `returns table`, `offers`, `offer results in reports`,
  `fallback: prospectus`, `source order`, `holdings count`, `nport cash`, `formula keys`, `derive`, `concentration`,
  `return series`, `fee schedule`. `source order` and `derive` run only when named.
- `--steps` can't be combined with `--fresh` or `--rebuild`. `--out <dir>` writes `<cik>.json` and
  `<cik>.coverage.json`.
- **Reading it back** (`bin/db.sh dev`): `facts_v2` by `{fundId: '<cik>', metric}`, then `extractorVersion` and
  `source`; `v2_readings` by `{cik, accession, group, promptVersion}`; `v2_source_picks` by
  `{cik, metric, subjectKey, periodStart, periodEnd}`. A `cik` query on `facts_v2` returns nothing.

## Gates before the PR
`bun test`, `bun run lint`, `bun run typecheck`, and the `MONGODB_DB=40act_test` integration runs for any writer
touched (Varay). Contracts in their own commit. Agrona's value check on the dev test funds is part of done.
