# Rulings

Product and data decisions that bind every value check and every change, newest first within each part. Florian rules
on product and data; Lawrence on finance definitions; Alfred decides engineering and relays both. Agrona keeps this
file current. A ruling that conflicts with a filing is raised through Arthur, never quietly changed.

## Sync v2: how values are chosen
- **Every value a model reading gives is served** (Alfred, 1 Nov 2026). He trusts the model's reading over code checks,
  which kept failing on layouts they hadn't seen.
  - The checks are recorded on the stored reading for review and stop nothing: the arithmetic for statements,
    highlights and offers, and for the returns table, the annual 1-year figure against the fiscal-year total return.
  - A value whose quote is not found in the filing is served unverified, on the model's own quote.
  - Accuracy is measured by random checks against the filings (Agrona).
- **Source order per key** (Florian's rule, kept by Alfred 31 Oct): the shareholder report (N-CSR/N-CSRS) first, then
  N-PORT, then the other forms (`packages/facts/src/syncV2/sourceOrder.ts`). Every losing reading is kept in
  `v2_source_picks` with whether it agreed.
- **Static keys** (Florian's list, 2 Nov): one value per fund and class, the newest filing of its source, never a
  series.
  - The list is `STATIC_KEYS` in `sourceOrder.ts`.
  - `investment_focus` (the Mandate) and `accredited_investor` are copied once, never extracted.
  - `cash_flow_period_start` stays dynamic (Alfred).
  - Nil's tag keys `management_fee`, `net_operating_expenses` and `amt_pay_one_yr_banks_borr` are dynamic
    (Alfred: "Don't make them static"). `monthly_flows` went on 4 Nov (Florian: one redemption metric).
- **A key read from one form tag takes the tag's name in snake_case** (Nil, 2 Nov; Florian's key plan, 3 Nov):
  N-CEN `managementFee` is `management_fee`. Exception, 6 Nov meeting: the N-CEN ticker is `share_class_ticker`, not
  `common_stock_ticker_symbol`.
- **Retired keys** (`packages/facts/src/syncV2/retiredKeys.ts`, `fallback.ts` `RETIRED_FALLBACK_KEYS`): sync v2 stops
  writing them and the source order step removes what is stored. 3 Nov: `holdings_footing_gap_pct`,
  `since_inception_cumulative_return_pct`, `disclosed_change`, `share_class_ticker` (the prospectus read). 4 Nov:
  `incentive_fee_ratio_pct`, `offer_proration_factor`, `nav_reporting_basis`. Professional's chapter 01 page reads
  `nav_reporting_basis` and `since_inception_cumulative_return_pct`, an open question (`professional.md`).
- **Blank stays blank** (Alfred, 30 Oct; refined 1 Nov). Never store 0 for a printed "None" or a missing item. A fee
  is 0 only when the filing states the fund charges none. A fee table's printed "None" alone is not that statement
  (Alfred, 3 Nov; Partners Group 1447247's Class I and M sales load).
- **No fallbacks on AQFID page 1's fee row** (Alfred, 2 Nov): only Nil's two N-CEN keys. Nil is removing the UI's
  other fallbacks.
- **No string or pattern matching for extraction** (Alfred). Readers use the structure (XML items, XBRL, tables) or a
  model.
- **Interval funds' pricing date stays blank** when the notice only says "normally the same as the deadline"
  (Alfred, 31 Oct).

## Professional keys: the 6 Nov 2026 meeting
The per-key decisions are on Nil's "V2 Keys To Add" page (`artifacts.md`) and in `professional.md`. The rules among
them:
- **Removed:** `distribution_discretion`, `minimum_investment`, `eighty_percent_policy`, `leverage_limit`,
  `shares_outstanding` (to discuss later) and `common_stock_ticker_symbol`. Removed keys stay on the page, struck.
- **One minimum:** a filing that states only "minimum investment" stores it as `minimum_investment_initial`.
- **Tickers:** `share_class_ticker`, from N-CEN (`commonStockTickerSymbol` per class), not `common_stock_ticker_symbol`.
- **`net_capital_transactions` becomes `net_inflows`:** computed from N-PORT Fund Info, subscriptions − redemptions.
- **`board_member_title`:** N-CEN's `isDirectorInterestedPerson`.
- **"Decide first" is gone** (Alfred): an overlap with an existing key is recorded as an audit note, not a gate.

## Lawrence, 2 Nov 2026 (AQFID pages 1–2)
- **Gains:** the statement's printed totals for every fund, currency lines included.
  - When no total is printed, sum every realized line.
  - For unrealized, sum every unrealized line plus `deferred_tax_unrealized`.
- **Cash** (`nport_cash_total`, from the newest N-PORT per period) = `cshNotRptdInCorD` + every STIV position's value
  + US Treasury debt (`assetCat` DBT, `issuerCat` UST) maturing within 90 days of the report date.
  - Alfred's details:
    - STIV counts except currency spot or forward contracts and securities-lending cash collateral;
    - no figure when the cash line is blank;
    - Treasury debt with no maturity is not counted.
  - It replaces the report's cash and short-term investments on page 2.
- **Calendar-year return** (page 1's "vs") runs January to December, compounded from N-PORT monthly returns. It is
  the value stored in `sl_peer_funds.calendar` that page 3 uses (Nil's UI), so `one_year_return_pct` is not needed
  there.

## Florian
- **4 Nov** (answers to "Sync v2 keys: open questions for Florian", `artifacts.md`; built the same day):
  - **One redemption metric:** N-PORT's `monthly_redemption_amount`, which AQFID page 2 sums over twelve months.
    Gone: `monthly_flows`, `offer_proration_factor`, the N-PORT offer formulas (`offer_amount_accepted_usd`,
    `offer_shares_accepted_check`) and the cap floor check. `repurchase_offers_per_year` (months with N-PORT
    redemptions) was tried and removed: it read 8 to 12 offers a year for 7 of 22 dev funds whose prospectus says
    quarterly.
  - `incentive_fee_ratio_pct` retires; the prospectus `incentive_fee_pct` stays.
  - `net_capital_transactions` is the report's statement of changes figure for a twelve-month column; N-PORT's sum
    is `net_capital_transactions_check`. For this key alone a column must foot to be served (Alfred). Renamed
    `net_inflows` on 6 Nov, see above.
  - An N-CEN NAV per share of 0 is no figure (a members' capital fund reports a total only).
  - Unfunded commitments come from the notes even when the word is missing: a commitment less its funded part; a
    master fund's Unfunded Commitments column; a column of N/A on every line is 0.
  - `total_return_pct_check` goes: the audited figure replaces N-PORT's. Where the highlights print a gross and a net
    total return, `total_return` is the net one.
  - A borrowings line printing a dash is 0 debt; no borrowings line is no figure.
  - `nav_reporting_basis` retires (the Dashboard no longer reads the return series).
  - **Standing rule:** the Dashboard and Compare use only keys the AQFID pages use, kept simple, with troublesome
    keys hidden. Their 1-year return is AQFID page 1's figure: twelve N-PORT monthly returns compounded to the newest
    month (Nil, `f9f9f8486`).
- **3 Nov: Professional Tier Key Sources,** his page (`artifacts.md`): for each Professional key keep, drop, replace,
  check or scope, with a source. Validate it against the filings and the code; never copy it. The 5 Nov audit of
  chapters 07–10 found problems in each chapter (`professional.md`).
- **2 Nov:** the static/dynamic split above. The Free keys were cut section by section with Alfred (rounds 1–6,
  `history.md`).
- **29 Oct** (Free value check answers):
  - **Certificate return:** the latest annual (1-year) return as printed in the latest N-CSR, N-CSRS or N-PORT,
    never calculated, Class I by default. Superseded on 30 Oct for page 1: it now leads with the trailing 12 months
    compounded from N-PORT, with the printed figure under it.
  - **Cash:** gross cash only, including escrow, excluding short-term investments. For page 2 this is superseded by
    Lawrence's rule.
  - **Expense ratio:** after waivers, including interest; none when not printed.
  - **Peer Benchmark share class:** always Class I; if none, Class S.
  - **Closed classes:** never quote a class closed to new investors; full 12 months of distributions.
  - **Compare:** "hide fees in the compare component". Not done: prod's Free policy still opens fees on Compare.
- **28 Oct:**
  - The Mandate (`investment_focus`) and the fund type on dev were entered by Florian by hand. They are correct,
    must not change, and are never flagged as defects against the filings.
  - They are to be copied from dev to prod, which is a prod write needing Alfred's approval.
  - Apollo S3 Private Markets (1978024) is an interval fund now, which its filings don't show yet; admins set the
    type in the UI.
- **26 Oct:** realized gains = investment lines only. Superseded by Lawrence on 2 Nov.
- **One class rule:** quote one class consistently (Class I) across a fund's figures.
- **23 Oct:**
  - **Insiders:** trustees who file Forms 3/4 as "Other: Trustee" count as insiders.
  - **Geographic and asset-class exposure:** % of total investments. Stored values stay as printed; the rebase is a
    read-time helper (deferred).
  - **Director fees:** all fees paid, the fund column, plus a note key with the fund-complex total.
  - **Expense-cap expiry:** the stated date ("through at least July 31, 2027" is 2027-07-31); withdrawn when no date
    is printed; no backfill.

  Reviewed (`hil_confirmed`) decisions outrank recalculated facts, so applying a ruling to existing data means
  re-deciding them.
- **23 Oct:** extraction runs on Gemini (3.8 Flash). The fact checker is skipped for model-read keys (the same model
  would check its own work) and kept for parser keys.
- **14 Oct** (AQFID/AQLID):
  - The AQLID build stays an admin batch, logging every decision.
  - No borrower AQFIDs: only the fund (AQFID) to loan (AQLID) link, with AQLIDs from N-PORT.
  - Consumer receivables are tracked as pools, one per N-PORT product label.
  - Mutual funds are ignored.
- **7 Sep:** `/funds` shows a tier's list intersected with the admin "Show" tick. That's not a bug.
- **NAV** (source rule): the N-CSR, N-CSRS, 10-K or 10-Q for its date, else N-PORT. One NAV rule for every reader
  (`packages/contracts/src/nav.ts`).

## Alfred: how the team works with data
- **Correct values first; no budget approvals for the key work on dev** (6 Nov 2026). Each key set is tested on a
  few funds and fixed before it spreads (`runbooks/add-a-key.md`). Prod and runs over every fund still ask.
- **Read the filing before calling a value wrong** (4 Nov): the stored copy in the bucket or the SEC page. A bounds
  check or two keys disagreeing is a lead, not a finding. Report misread vs genuine with the quoted line.
- **Link the filing behind every figure** in a write-up for Alfred or Florian (4 Nov): `primaryDocumentUrl` from
  `filings` by accession, on the fund or figure it supports.
- **Prod is updated after dev is done** (4 Nov): a prod blank from a step not yet run there is known, not a finding.
- **Key work in order** (5 Nov): find every key in use, compare with Florian's plan, lock the list, then code.
  Record code bugs met during an inventory; don't stop to fix them.
- **Pages and questions for others** (5 Nov): only what the reader needs, detail behind a click. A question says
  what is proposed, what goes wrong (with the number that shows it), then the question, in everyday words.
- Tell him before any run that calls a model or writes beyond what he named (an ingest, a batch, a rebuild), with
  the funds and the cost, and wait.
- "Verified" must mean every served value is right. Never keep a known-wrong value because a rule said keep.
- Check provenance (model, version, dates, what a count counts) before evidence goes to Florian.
- Say what was checked live on SEC and what was read from stored copies, in neutral words.
