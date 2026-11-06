# Professional keys

The current workstream (from 6 Nov 2026). Professional is the research tier the code calls `standard`. The goal: every
key the Professional pages show is served by sync v2 (`facts_v2`) and correct, set by set, so the pages can move off
v1. Today the Professional pages read v1 `facts`. Rules: `rulings.md`; how a key is built: `runbooks/add-a-key.md`.

## How the work runs (Alfred, 6 Nov 2026)
For each set of keys, starting with the simple parser keys:
1. Add the key and its definition, with its sources.
2. Add it to the reader's prompt or the parser.
3. Sync one fund with the CLI.
4. Test on a few other funds, and check the values against the filings.
5. Expand to the dev test funds (below), fix what is wrong, and lock the set.
6. Next set.

- **The named source may be wrong.** The documents Nil's and the 07–10 maps name may not hold the value: look in the
  filings before building (Agrona). Record where the value really is.
- **Correct values first, no budget approvals** for this work on dev (Alfred, 6 Nov). Prod and runs over every fund
  still ask.
- **One list, one owner.** Nil's "Key Master List" is the reference: every key on prod, the keys to add, removed,
  left out, and those the code writes that prod doesn't have yet. His "V2 Keys To Add" holds the to-add rows with
  the 6 Nov decisions (`artifacts.md`). Decisions come from Alfred
  through Arthur; change the page only when he asks.
- **The dev test funds,** the 27 funds sync v2 has run on dev (6 Nov): 1076673 Xanthus, 1186641 A&Q Long/Short,
  1475457 GCM Grosvenor, 1543188 AB Multi-Manager, 1609211 AMG Pantheon, 1616203 Pomona, 1676197 Apollo Diversified
  Credit, 1688554 PIMCO Flexible Credit, 1688897 FS Credit Income, 1762562 Clarion Partners, 1803491 Hamilton Lane,
  1830926 Emery Partners, 1830974 Aspiriant, 1864609 Cascade, 1876006 Ares Private Markets, 1885778 John Hancock
  Marathon, 1899610 Carlyle AlpInvest, 1905379 Innovation Access, 1918642 StepStone Venture & Growth, 1930054
  Blackstone PE Strategies, 1940499 JPMorgan Private Markets, 1955857 Brookfield Infrastructure, 1978024 Apollo S3,
  2036029 83 Investment Group, 2059436 Blue Owl Alternative Credit, 2061233 Morgan Stanley PMA-Balanced, 853180
  Invesco Senior Loan.

## Batch order (Alfred, 6 Nov 2026)
Start with batch 1. Each batch goes through the loop above before the next starts. A rename goes in the batch whose
code it touches.

| # | Batch | Keys | Why here |
|---|---|---|---|
| 1 | N-CEN tags | `share_class_ticker` (back, renaming `common_stock_ticker_symbol`), `is_non_diversified_company`, `rule_19a1_notice_flag` | One file (`tagKeys.ts`), one writer bump; exact values. `isPaymentDividend` sits at two paths (below) |
| 2 | Prospectus iXBRL + N-PORT | `expense_example_1y`, `_3y`, `_5y`, `securities_act_file_number`, `net_assets_end_of_period` | `prospectusXbrl/conceptMap.ts:33-36` already maps all four expense examples and v1 holds about 840 rows of each on dev, but sync v2 writes none: find where it drops them first. File number: try the prospectus cover's `dei:EntityFileNumber` before Form 24F-2NT |
| 3 | Computed from stored rows | `advisory_fee_expense`, `net_inflows` (rename), `board_independence_pct`, `change_alert_flag`, `fund_interest_pct`, `direct_holding_pct` | Formula keys, no reads. `net_inflows` waits on open question 7; the two swaps on question 4 |
| 4 | Report keys the stored readings already hold | `expense_waiver_amount`, `audited_gross_expense_ratio_pct` | Code only, no model reads: the statements reading has an `expense_waiver` row, the highlights reading the before-waivers ratio |
| 5 | Report keys needing prompt changes | `interest_expense`, `total_investments_cost`, `distributions_received_from_investments`, `incentive_fee_paid`, `manager_stated_return_pct`, `manager_stated_return_basis`, then `total_return_delta_bps` | Each prompt bump re-reads the reports, so one bump per reader. Cash flow rows are `other` today and interest has no role (picking it by label would be pattern matching), so they need new roles. If purchases and sales are decided first, add them to the same statements bump |
| 6 | Prospectus model reads | `eligible_investors`, `minimum_investment_initial`, `minimum_investment_subsequent`, `nav_frequency`, `distribution_policy`, `regulatory_classification`, `tax_reporting_form`, `incentive_fee_crystallization`, `incentive_fee_high_water_mark`, `temporary_borrowing_limit`, `valuation_governance`; `repurchase_cap_pct`'s new sources (Schedule TO-I, Rule 23c-3 notices) | A new key re-reads the whole prospectus, so all together, read once. The meeting's tag check (N-2 tags) comes first and may move two keys to batch 8 |
| 7 | People rows | `board_member_biography`, `portfolio_manager_title`, `portfolio_manager_since`, `portfolio_manager_biography`, then `portfolio_manager_count` | One row per person, often in the SAI, sometimes a separate document: find where first |
| 8 | Tagged prospectus sections | `transferability`, `dividend_reinvestment_plan`, `early_repurchase_fee`, `liquid_assets_sleeve_policy` | New code: no step reads a tagged text block today. Plan with Arthur |
| 9 | New form lanes | 13D/13G/Form 4: `owner_shares`, `owner_class`, `owner_pct_of_class`, `owner_is_ten_pct_filer`, `owner_source_form`, then `block_holder_count`. Forms 3/4/5: `insider_count`, `insider_total_shares`, then `insider_holdings_usd` | The most new code: these forms are not read today |
| Later | After their decisions | the 7 facility keys; `purchases_of_investments`, `sales_of_investments`, then `prr_12m`, `prr_36m`; `repurchase_allocation_rule`, `repurchase_unfilled_request_treatment`; `expense_example_10y` | Discuss later (6 Nov meeting) |

**Held out of the batches** until Alfred decides:
- `board_member_title`: open question 5. It would also be the first one-row-per-director key outside v1's board lane.
- `coinvest_pct`: it sorts holdings by their names, against the no-pattern-matching rule (`rulings.md`).
- `repurchase_cadence_observed`: close to the months-with-redemptions count removed on 4 Nov (open question 4).
- `owner_pct_of_fund`: needs `shares_outstanding`, removed on 6 Nov (open question 9).
- Chapter 01's two retired keys (open question 2): small, can ride with any batch once decided.

**Nothing to build:** the 10 keys the code writes that prod doesn't have yet (Nil's master list) arrive at the next
prod run; the 6 retired keys still on prod go at the next prod run.

## The pages and what Professional sees
- **Chapters 01–06** (Valuations, Liquidity, Portfolio, Leverage, Flows, Returns): mapped by Nil, one page each
  (`artifacts.md`). Data points: `apps/web/lib/standard-view/models/<chapter>DataPoints.ts`. 24 new keys.
- **Chapters 07–10** (Prospect: Structure & wrapper, Fees & cost, Governance & interests, Compliance;
  `apps/web/lib/standard-view/chaptersProspect.ts`): mapped on 5 Nov from each builder's `requestedKeys` and data
  points, traced twice, compared with Florian's plan. 61 new keys.
- **Not mapped by either:** the Overview and Fund metrics pages, both open to Professional.
- **The tier policy decides what counts.** Prod's `research_access_revisions` (family `SL`, version 2), column
  `standard`:
  - hidden: `aq-score`, `aqmid`, `aq-report`, `AQS-decomposition`, `2I`, `1H`, `3BP`, `FM-window`, `FM-C`;
  - locked (locked tabs are dropped, not shown): `RC-your-client`, `RC-provenance`, `RC-affiliated`,
    `RC-conflicts`, `RC-person-grounding`, `RC-stress-lab`, `trends`, `risk`, `decision-value`, `news`,
    `3AO`–`3AT`, `OV-changed-since`, `OV-direction`, `3J`, `3D`, `3BH`, `3AU`, `3G`, `3K`, `3AG`, `3BL`, `3AV`,
    `3AW`, `3W`;
  - `compliance-brief` shows a summary; every other item is open.
  - Drawers carry evidence `platform`, so they are Research-only: a key read only in a drawer is not a Professional
    key (`offer_price_basis`, `facility_commitment_fee_step_pct` and `_terms`, `liquidity_coverage_*`).

## The list on 6 Nov 2026
78 rows: 72 to add, 6 removed (kept on the page, struck), 13 to discuss later. None was on prod `facts_v2` (203
keys) on 6 Nov. Built in the code but not on prod: `repurchase_cap_pct`, `net_capital_transactions_check`. Left out
of the list, with the page's reasons: `disclosed_change`, `fund_structure`, `incentive_fee_ratio_pct`,
`repurchase_mechanism`, `repurchase_frequency`, `diversification_status`, `access_types`, `director_fees_total`,
`board_member_compensation`, `net_capital_transactions` (now `net_inflows`), and Florian's 7 drops
(`anti_dilution_mechanism`, `class_is_seeded`, `incentive_fee_catch_up_pct`, `incentive_fee_hurdle_pct`,
`portfolio_manager_role`, `repurchase_class_priority`, `subscription_frequency`).

| Key | Status | Step | Method | 6 Nov decision |
|---|---|---|---|---|
| `board_member_biography` | to add | prospectus read | LLM |  |
| `distribution_discretion` | removed | prospectus read | LLM | Remove. |
| `distribution_policy` | to add | prospectus read | LLM | Prospectus, probably not N-PORT. |
| `eligible_investors` | to add | prospectus read | LLM | Prospectus or SAI. |
| `incentive_fee_crystallization` | to add | prospectus read | LLM |  |
| `incentive_fee_high_water_mark` | to add | prospectus read | LLM |  |
| `minimum_investment` | removed | prospectus read | LLM | Remove. Where the filing states only a minimum investment, that value goes into minimum_investment_initial. |
| `minimum_investment_initial` | to add | prospectus read | LLM | Keep, as the one key for the minimum initial. Where the filing states only a minimum investment, that value goes here. |
| `minimum_investment_subsequent` | to add | prospectus read | LLM |  |
| `nav_frequency` | to add | prospectus read | LLM |  |
| `portfolio_manager_biography` | to add | prospectus read | LLM |  |
| `portfolio_manager_since` | to add | prospectus read | LLM |  |
| `portfolio_manager_title` | to add | prospectus read | LLM |  |
| `regulatory_classification` | to add | prospectus read | LLM | Keep. It is essentially the fund type, which we already have. |
| `repurchase_allocation_rule` | to add, discuss later | prospectus read | Split | To discuss later. |
| `repurchase_cap_pct` | to add, built (not on prod) | prospectus read | LLM | Model read: prospectus; Schedule TO-I for tender-offer funds; Rule 23c-3 notices for interval funds. |
| `repurchase_unfilled_request_treatment` | to add, discuss later | prospectus read | Split | To discuss later. |
| `tax_reporting_form` | to add | prospectus read | LLM |  |
| `temporary_borrowing_limit` | to add | prospectus read | LLM | Prospectus / N-2: see if they have tags (20–25). |
| `valuation_governance` | to add | prospectus read | LLM | Prospectus / N-2: see if they have tags (20–25). |
| `dividend_reinvestment_plan` | to add | tagged prospectus section (new code) | LLM | Prospectus. Prospectus / N-2: see if they have tags (20–25). |
| `early_repurchase_fee` | to add | tagged prospectus section (new code) | LLM | Prospectus / N-2: see if they have tags (20–25). |
| `eighty_percent_policy` | removed | tagged prospectus section (new code) | LLM | Remove. |
| `leverage_limit` | removed | tagged prospectus section (new code) | LLM | Remove. |
| `liquid_assets_sleeve_policy` | to add | tagged prospectus section (new code) | LLM | Prospectus, investment objectives. Prospectus / N-2: see if they have tags (20–25). |
| `transferability` | to add | tagged prospectus section (new code) | LLM | Keep (the plan already says Keep). Prospectus / N-2: see if they have tags (20–25). |
| `facility_commitment_fee_pct` | to add, discuss later | N-CSR notes | LLM | Keep. To discuss later. |
| `facility_commitment_fees_paid` | to add, discuss later | N-CSR notes | LLM | Keep. To discuss later. |
| `facility_covenants` | to add, discuss later | N-CSR notes | LLM | Keep. To discuss later. |
| `facility_interest_rate_pct` | to add, discuss later | N-CSR notes | LLM | Keep. To discuss later. |
| `facility_is_secured` | to add, discuss later | N-CSR notes | LLM | Keep. To discuss later. |
| `facility_maturity_date` | to add, discuss later | N-CSR notes | LLM | Keep. To discuss later. |
| `facility_purpose` | to add, discuss later | N-CSR notes | LLM | Keep. To discuss later. |
| `incentive_fee_paid` | to add | N-CSR notes | LLM | N-CSR. |
| `distributions_received_from_investments` | to add | N-CSR statements | LLM | N-CSR. |
| `expense_waiver_amount` | to add | N-CSR statements | LLM | N-CSR and prospectus. |
| `interest_expense` | to add | N-CSR statements | LLM | N-CSR. |
| `purchases_of_investments` | to add, discuss later | N-CSR statements | LLM | N-CSR. Might need a formula. To discuss later. |
| `sales_of_investments` | to add, discuss later | N-CSR statements | LLM | N-CSR. To discuss later. |
| `shares_outstanding` | removed, discuss later | N-CSR statements | LLM | Remove. To discuss later. |
| `total_investments_cost` | to add | N-CSR statements | LLM |  |
| `audited_gross_expense_ratio_pct` | to add | Financial Highlights | LLM | N-CSR. Check whether XBRL tags are present. |
| `manager_stated_return_basis` | to add | Financial Highlights | LLM | N-CSR. |
| `manager_stated_return_pct` | to add | Financial Highlights | LLM | N-CSR. |
| `expense_example_10y` | to add, discuss later | prospectus iXBRL | Parse | To discuss later. |
| `expense_example_1y` | to add | prospectus iXBRL | Parse |  |
| `expense_example_3y` | to add | prospectus iXBRL | Parse |  |
| `expense_example_5y` | to add | prospectus iXBRL | Parse |  |
| `board_member_title` | to add | N-CEN parser | Parse | Read from N-CEN: isDirectorInterestedPerson. |
| `common_stock_ticker_symbol` | removed | N-CEN parser | Parse | Remove. share_class_ticker (N-CEN) instead. |
| `is_non_diversified_company` | to add | N-CEN parser | Parse |  |
| `rule_19a1_notice_flag` | to add | N-CEN parser | Parse |  |
| `share_class_ticker` | to add | N-CEN parser | Parse | Put back, read from N-CEN, in place of common_stock_ticker_symbol. |
| `net_assets_end_of_period` | to add | N-PORT parser | Parse | N-PORT. |
| `insider_count` | to add | new form lane | Parse |  |
| `insider_total_shares` | to add | new form lane | Parse |  |
| `owner_class` | to add | new form lane | Parse |  |
| `owner_is_ten_pct_filer` | to add | new form lane | Parse |  |
| `owner_pct_of_class` | to add | new form lane | Parse |  |
| `owner_shares` | to add | new form lane | Parse |  |
| `owner_source_form` | to add | new form lane | Parse |  |
| `securities_act_file_number` | to add | new form lane | Parse |  |
| `advisory_fee_expense` | to add | computed | Computed |  |
| `block_holder_count` | to add | computed | Computed |  |
| `board_independence_pct` | to add | computed | Computed |  |
| `change_alert_flag` | to add | computed | Computed |  |
| `coinvest_pct` | to add | computed | Computed |  |
| `direct_holding_pct` | to add | computed | Computed |  |
| `fund_interest_pct` | to add | computed | Computed |  |
| `insider_holdings_usd` | to add | computed | Computed |  |
| `net_capital_transactions_check` | to add, built (not on prod) | computed | Computed |  |
| `net_inflows` | to add | computed | Computed | Rename net_capital_transactions to net_inflows, computed from N-PORT Fund Info: subscriptions − redemptions. |
| `owner_pct_of_fund` | to add | computed | Computed |  |
| `portfolio_manager_count` | to add | computed | Computed |  |
| `prr_12m` | to add | computed | Computed |  |
| `prr_36m` | to add | computed | Computed |  |
| `repurchase_cadence_observed` | to add | computed | Computed |  |
| `total_return_delta_bps` | to add | computed | Computed |  |

## Open questions (raise through Arthur before building the key they touch)
1. **`fund_structure`** is left out as "not a key", but the page reads it: `masthead/buildIdentity.ts:57`,
   `models/structureOverview.ts:106`, `models/structureRegistration.ts:58`, `ContextLine.tsx:18`. It is not in
   `facts_v2`.
2. **Chapter 01 needs two retired keys,** `nav_reporting_basis` and `since_inception_cumulative_return_pct`
   (`retiredKeys.ts:12`). Prod `facts_v2` still holds their old rows; the list omits them. Un-retire, or change
   the page?
3. **Research findings on Professional.** `total_operating_expenses` is read only by the findings sentence
   (`returnsResult.ts:146–157`). Nil left findings out; the 07–10 map counts the keys findings read. Chapter 10's
   Research findings prints the stored risk register (`sl_risk_register`, no sync v2 version, about 154 more keys):
   retire it or rebuild it on sync v2. One rule for both.
4. **Florian's swaps change what the page shows:** trustee pay becomes `board_independence_pct` (against his 23 Oct
   ruling to show fees paid); `repurchase_frequency` and `repurchase_mechanism` become `repurchase_cadence_observed`
   (the formula writer tried a months-with-redemptions count on 4 Nov and removed it: 8 to 12 "offers" a year for 7
   of 22 dev funds); `disclosed_change` becomes `change_alert_flag` (the Filing changes tab is built on it).
5. **`board_member_title` from `isDirectorInterestedPerson`** holds what `board_member_affiliation` already reads.
   N-CEN has no title: each director has only `directorName` and that flag.
6. **`net_assets_end_of_period` from N-PORT** gives the fund total, which `total_net_assets` already serves. The page
   reads it per share class: the class pick (`apps/web/lib/aqreview/ledger.ts:382`), "not yet seeded"
   (`identity.ts:550`) and the Financial Highlights table. The highlights read already asks the model for each
   class's `net_assets_end` (`highlightsPrompt.ts:47`) and serves no key from it. Alfred, 6 Nov: leave the N-PORT
   decision as it is for now.
7. **`net_inflows`:** the meeting lists reinvestments as a source, but the formula is subscriptions − redemptions.
   `net_capital_transactions_check` already works out sales + reinvestments − redemptions from the same N-PORT rows
   (`monthly_sales_amount`, `monthly_reinvestment_amount`, `monthly_redemption_amount`).
8. **`share_class_ticker`:** keeping the name means renaming `tagKeys.ts`' `common_stock_ticker_symbol` back. Prod's
   300 old rows (105 semi-liquid funds) came from the prospectus read retired on 3 Nov.
9. **`owner_pct_of_fund`** divides each holder's shares by `shares_outstanding`, which the meeting removed (to
   discuss later).
10. **Chapter 06** drops the tax-character and return-of-capital rows (Alfred's answer), though Florian's plan keeps
    4 of those keys: tell Florian.

## Facts already checked (6 Nov 2026)
- N-CEN's 19a-1 field `isPaymentDividend` sits at two paths: top level (Ares, StepStone) and
  `paymentDividendSeries.isPaymentDividend` (YieldStreet; fixtures in `packages/facts/src/governance/fixtures/`).
  A parser must read both.
- N-CEN `management_fee` is a percentage (Item D.8), so `advisory_fee_expense` = `management_fee` ×
  `monthly_average_net_assets` works.
- `expense_ratio_pct` takes the after-waivers row, the before-waivers row only when no other prints
  (`highlights.ts:144–145`).
- `prr_12m` and `prr_36m` come from derive (`computeDerivedDrafts.ts`, `derivationNotes.ts:276–279`), which sync v2
  runs.
- `net_realized_gain_loss` is the printed total, currency and derivative lines included (`statementValues.ts:9`).
- `ytd_return_pct` is never printed: it only marks the classes that file returns (`basisClass.ts:66–75`).
