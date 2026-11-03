# Verifying a value against the filings

Agrona's method. A value is a claim; the filing is the witness. The output is a verdict per value (right, wrong,
stale, missing, or a ruling case) with the accession and the verbatim text.

## 1. What do we serve?
- **Which collection:** the AQFID page reads `facts_v2`; other pages still read `facts`. Read the newest row per series:
  ```
  /Users/alfredamoah/AltQ/team-altq/bin/db.sh prod --eval 'db.facts_v2.find({fundId:"2061233", metric:"holdings_count"}).sort({createdAt:-1}).limit(3).toArray()'
  ```
  Use `dev` for dev. The fact's `source` carries the accession, the locator, the quote and the extractor version.
- **What a reader sees:** the API decides with `latestFacts`. What the page shows is what counts, not what a review
  ranked. When in doubt, ask Ellie for a screenshot.
- **Which rows are served:** for sync v2, `v2_source_picks` holds the readings that lost to the source order, with
  whether they agreed.

## 2. What does the filing say?
- **Our stored copy:** `gcloud storage ls gs://act-498418-sec-raw/<cik>/<accession>/`, then `gcloud storage cat` the
  normalized `norm/norm-v2/<file>.md`, or the raw file. The catalog (`filings` in the database) lists each
  accession's files.
- **SEC itself:** `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<cik>` and the filing index, with
  `curl -A 'AltQ Research aamoah@altq.ai'`, under 10 requests a second.
- **Which filing is in force:** the newest of its form for the period. An amendment (`/A`) replaces its original.
  N-PORT is monthly data filed quarterly. N-CEN is annual.
- **Form items that come up:**

| Item | Where |
|---|---|
| N-PORT cash | `cshNotRptdInCorD` |
| N-PORT short-term investments | STIV positions (`assetCat`) |
| Borrowings due within a year | N-PORT B.2 (`amt_pay_one_yr_banks_borr`) |
| Monthly flows | N-PORT B.6 |
| Management fee and net operating expenses | N-CEN D.8 and D.9 |

## 3. The verdict
- **Right / wrong / stale** (a newer filing says otherwise) / **missing** (the filing has it, we don't) / **blank
  is right** (the filing doesn't print it: blank stays blank).
- **A ruling case:** the filing fits no ruling in `../rulings.md`. Write it up for Arthur with the options. Don't
  invent a rule.
- **Is it one fund or a pattern?** Check two or three other funds of the same form shape before calling it a rule
  problem.

## Rules
- "Verified" means every value called right is right. Never keep a known-wrong value because a rule said keep.
- **Anything going to Florian:**
  - check provenance first: which extractor or model version, over which dates, and what a count counts;
  - say neutrally which filings you opened on SEC and which you read from our copies. A stored accession is the
    same document.
- **Admin-entered data is correct by definition:** Florian's Mandates and fund types (Apollo S3 1978024 is
  interval).
- **Keep sweeps small and sequential** on the dev cluster, and isolate Cliffwater 1735964.
