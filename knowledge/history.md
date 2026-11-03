# History before the team

What was built on 40act before this team existed (to 3 Nov 2026), by workstream, newest first. It was distilled from
Alfred's Claude sessions and their saved memories. For detail, check `git log` on the branches named here. The journal
carries on from 2026-11-03.

## Sync v2: the new extraction flow (30 Oct to 3 Nov 2026, branch `feature/new-sync`)
- **Why:** on 30 Oct Alfred scrapped the per-fund Claude value-check skill, because each run found new issues. The
  Free launch moved a week, and the plan became a mostly programmatic sync.
  - Florian's plan: per-key source rules, the fiscal-year calendar, XBRL and XML first, and a model only for what
    those can't give.
- **Design:** a sibling collection `facts_v2` (with `extraction_runs_v2`, `derive_abstentions_v2`, `v2_readings`,
  `v2_source_picks`), leaving the current sync untouched. CLI only: `apps/worker/src/cli/sync-v2.ts`. A fund's run
  has these steps:
  - the existing lanes: N-PORT, N-CEN, the prospectus fee table (XBRL), and Nil's tag keys;
  - the model readers (Gemini 3.8 Flash): highlights, statements and the returns table from the shareholder report,
    offers from the SC TO-I and N-23C3A filings, offer results in reports (notes), and a prospectus fallback for
    keys no report gave;
  - then source order, holdings count, N-PORT cash, derive and concentration.
- **Results:**
  - 13 answer-key funds: 199 right, 5 wrong, 19 blank of 223 (the current flow: 192/20/11). 30 of 30 random values
    were right.
  - 23 test funds on dev: 1,406 of 1,725 Free key and fund pairs have a value.
- **2 Nov:**
  - The `facts_v2` indexes cut a derive pass from 140 s to 4.8 s.
  - Static keys.
  - The N-CEN fiscal year end from stub periods.
  - The purge keeps copied (manual) rows.
  - Lawrence's gains and N-PORT cash.
  - The Free keys were streamlined with Florian in rounds 1–6, tracked in the Structured Data Coverage page
    (`artifacts.md`).
  - Batch mode for an unattended VM: replay by default (a stored reading costs $0), `--concurrency`, `--resume`, a
    storage check before every fund, failed funds kept for resume.
  - Runs anywhere: only the `_v2` suffix is checked, and each run copies the canonical twins' indexes first.
  - A missing Google key file no longer shows as "missing from storage".
- **3 Nov:**
  - Prod's v2 collections were indexed (mongosh, on Alfred's yes).
  - Alfred started the prod batch on his Windows VM: 263 funds (the two AIP Alternative Lending Funds, 1709447 and
    1709406, skipped as too large, at Nil's word), 4 at a time, `--resume`.
  - A test on 2061233 cost $1.05 and took about 8 minutes; its second run replayed at $0.
- **Known:**
  - The offer-results step re-adds 2–6 rows a run that source order then removes: churn, net zero.
  - Derive writes a new revision when a value's explanation changes, even if the value is the same. That is not a
    duplicate.
  - Innovation Access (1905379) has no N-CEN.
  - Holding rate and maturity are on 14 of 23 test funds, which is expected.
  - Unverified blanks: inception for Xanthus (1076673) and Invesco (853180); holding asset category for A&Q, GCM and
    AMG; 2061233 shows a category on 1 of 14 holdings.
- **Nil** builds the UI side (the AQFID page reads `facts_v2` alone) and continues the sync from the handoff doc
  (`artifacts.md`).

## Free launch (27 to 31 Oct 2026, `feature/free-version-prep`, `fix/free-launch-display`)
- **Decision (27 Oct):**
  - Free first, Standard about a week later.
  - The upgrade parts are commented out, and Free gets a smaller side nav.
  - A fund opens its AQFID certificate (`/{slug}/{cik}/dossier/aqfid`, 4 pages).
- **Performance:** the deployed cold load went from 12.6 s to about 3 s locally (scalar read bounds, one-query axes
  reads, a parallel holdings read with a 60 s cache).
- **The Free View Key Map** (28 Oct) traced which fact keys reach each Free page, with a harness that drops keys one
  at a time.
- **The Free value check** on 10 funds (227 values) led to Florian's rulings of 28–29 Oct. 40actdev web deploys
  failed from 27 Oct, when `next build` ran out of memory.
- **Dev fund lists** were wiped by integration tests on 27 Oct and restored (`runbooks/integration-tests.md`).

## Model choice (23 Oct 2026)
- Florian chose Gemini (3.8 Flash) for extraction, on comparisons that turned out to measure Gemini 3.1 Pro
  (`facts_legacy`). Flash itself was unmeasured then.
- The checker is skipped for model-read keys. Qwen was trialled in September and October.

## AQ Report (20 to 22 Oct 2026, `feature/aq-report`)
- The report engine (Alfred's) is pinned to `modelForReport()`, gemini-3.8-flash. A run on dev cost $9.77 over 10 min.
- **Admin report editing** (PR #333, merged): a save inserts an edited copy.
- **Score narrative editing** (Proof, Prospect, Pulse): edits are pinned to a score run and applied on read.
- **Report prompts in Mongo:** 33 `aq_prompts` rows under schema `aq-report`, with the `promptsDigest` stamped.
- **Report figures:** the top-10 ranks the deduplicated book, and the concentration figure is computed first.
- **Open:** prod migrations before deploy; the tab's `?asOf=` is ignored by the report route.

## AQFID and AQLID identity (14 to 15 Oct 2026, `feat/aqfid-aqlid`)
- **The audit:** N-PORT `lei_`/`cusip_` keys never linked look-through holdings.
- **The AQLID** concept was sound, but the N-CSR lane minted duplicates.
- **Built:**
  - phases 1–4: N-PORT keys attach, merges, the N-PORT-only AQLID build, receivable pools;
  - PR #293 merged, follow-up PR #295.
- **Open:**
  - admin merges for Peer Holding III, Auris Luxembourg III and TK Elevator USD;
  - first syncs for Bow River and SP-11101;
  - the prod migration and AQLID build.

## Research tiers and self-serve accounts (8 to 22 Oct 2026, `feat/tiers`)
- **Tiers** (PR #267): Free, Standard and Research (stored `platform`); per-tier fund lists; the policy editor;
  staff "Preview as"; fund chat for Research only.
- **Accounts:** five slices, all on `feat/tiers`.
  - S1: forgot password.
  - S2: sign-up through the Auth0 Management API, with email verification.
  - S3: `/plans` and `/account`.
  - S4: Stripe checkout (sandbox, test mode).
  - S5: the customer portal.
- **First visit:** welcome plans and a dashboard tour.
- **Emails** go through Auth0's Resend integration (from support@altq.ai), because SendGrid was blocked.
- **No CAPTCHA** (Alfred): rate limits only.
- **Stripe:** the live account doesn't exist yet (Lawrence), and Stripe's variables are kept out of the prod build
  config.

## NAV (7 Oct 2026, `feat/nav-nport-quarters`)
- N-PORT every quarter; BDC NAV from XBRL; one NAV rule for all readers (`packages/contracts/src/nav.ts`); NAV gap
  conflict proposals; `bun run check:nav`.
- **Open:**
  - the PR;
  - the prod rollout (migrate, XBRL balance backfill, N-PORT backfill, prompt re-seed, `nav-statement-rerun`);
  - the deferred "as-of note" next to the NAV.

## InvestCloud (6 to 19 Oct 2026)
- ModelIQ asked for six CSV feeds. The field map was audited against prod: 74 fields, 11 gaps.
- **Blockers:** 61 of 65 BDCs have no facts; N-PORT class returns are anonymous for 240 of 264 funds; no CUSIPs.
- **Plan:** extend `apps/public-api`, then feeds.
