# Backlog

Deferred work, each with what would bring it back. Arthur adds what Alfred defers; Kezess adds clean-up candidates.
When an item is picked up, it leaves this file for the journal.

## Sync v2
- [ ] **Copy the static keys on prod:** Mandates (`investment_focus`) and `accredited_investor` into prod's
  `facts_v2` from prod's own canonical facts. Until then those keys are blank on prod. Brings it back: the prod
  batch finishing. Needs Alfred's yes (a prod write).
- [ ] **Re-run the funds with a failed step** from the VM batch (`*.failed.json`), with `--steps` for just the
  failed step. Brings it back: the batch finishing.
- [ ] **Stop extracting the keys struck in the streamlining rounds** (the v2 extraction update). Brings it back:
  Alfred's word that the Free key list is final.
- [ ] **v2's stored peer documents** (Alfred: "we can handle 2 later").
- [ ] **Unverified blanks:** inception for Xanthus 1076673 and Invesco 853180; holding asset category for A&Q, GCM,
  AMG and 2061233 (1 of 14 holdings). Agrona.
- [ ] **A worker job for sync v2** (it is CLI only).
- [ ] **Re-convert prod's lost-table documents** (norm-v3).
- [ ] **The offer-results churn:** 2–6 rows re-added each run, then removed by source order.

## Waiting on Florian or Nil
- [ ] Compare still shows the FY return and the latest offer cards, and fees are not hidden on Compare (Florian
  asked on 29 Oct).
- [ ] Nil's UI: the fee row, the calendar year from `sl_peer_funds`, `nport_cash_total`, `monthly_flows`,
  `amt_pay_one_yr_banks_borr`, Sources & notes, no fallbacks.

## Older workstreams
- [ ] **NAV:** the PR, the prod rollout, then the "as-of note" (raise last).
- [ ] **AQ Report:** prod migrations before deploy; the report route ignores `?asOf=`.
- [ ] **AQFID/AQLID:** admin merges, Bow River and SP-11101 first syncs, the prod migration and AQLID build.
- [ ] **Tier scopes:** a guard in `setTierScopes` that refuses a non-test database. Brings it back: touching tier
  scopes or that test kit.
- [ ] **Dev cluster load:** bound the holdings read by period, fix the scalar-read plan on 1735964, archive superseded
  fact revisions.

## Clean-ups
Kezess adds candidates here: path, what to delete or fold, and why. Gideon takes them as their own changes.
