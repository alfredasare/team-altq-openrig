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
  - Nil's tag keys `management_fee`, `net_operating_expenses`, `amt_pay_one_yr_banks_borr` and `monthly_flows` are
    dynamic (Alfred: "Don't make them static").
- **Blank stays blank** (Alfred, 30 Oct; refined 1 Nov). Never store 0 for a printed "None" or a missing item. A fee
  is 0 only when the filing states the fund charges none.
- **No fallbacks on AQFID page 1's fee row** (Alfred, 2 Nov): only Nil's two N-CEN keys. Nil is removing the UI's
  other fallbacks.
- **No string or pattern matching for extraction** (Alfred). Readers use the structure (XML items, XBRL, tables) or a
  model.
- **Interval funds' pricing date stays blank** when the notice only says "normally the same as the deadline"
  (Alfred, 31 Oct).

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
- Tell him before any run that calls a model or writes beyond what he named (an ingest, a batch, a rebuild), with
  the funds and the cost, and wait.
- "Verified" must mean every served value is right. Never keep a known-wrong value because a rule said keep.
- Check provenance (model, version, dates, what a count counts) before evidence goes to Florian.
- Say what was checked live on SEC and what was read from stored copies, in neutral words.
