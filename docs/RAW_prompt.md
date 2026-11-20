You are building a payments reconciliation tool for a take-home assessment (2 hours, evaluated on judgment, edge-case thinking, and verifiability, not feature count). Build ONLY what is needed, but make it correct and demonstrable. Work in small verified steps: write tests first for each module, run them, fix, then move on.

## PROBLEM
A payments company's books don't balance at month end. The platform records a transaction instantly at payment time. The bank batches and settles funds 1-2 days later. At month end every transaction should have a matching settlement, but they don't. Find out WHY and SHOW WHERE the gaps are.

## STACK (fixed, do not deliberate)
- Python 3.11, FastAPI backend, pandas optional, `decimal.Decimal` for ALL money (never float).
- Single-page dashboard served by FastAPI (vanilla JS + Chart.js via CDN, no build step). 
- pytest for tests. Dockerfile for deploy (Render/Railway/Fly). SQLite not required; use CSV files + in-memory processing.
- Repo layout: `app/generator.py`, `app/reconcile.py`, `app/main.py`, `app/static/index.html`, `data/` (generated CSVs + `ground_truth.json`), `tests/`, `README.md`, `ASSUMPTIONS.md`, `TESTS.md`, `PRODUCTION_RISKS.md`, `Dockerfile`, `requirements.txt`.

## STEP 1: ASSUMPTIONS (write ASSUMPTIONS.md first, and surface them in the UI)
State and implement these (change only if you can justify it):
1. Currency INR, reconciliation month = October 2026. Timestamps in UTC; the bank's cutoff is also UTC. (Note IST/UTC boundary risk.)
2. Platform amounts are stored to 3 decimals (e.g. tax/fee splits); bank amounts are rounded half-up to 2 decimals per line.
3. Settlement lag is 1-2 calendar days; weekends push to the next business day.
4. Settlement is gross of fees (fees ignored) to keep scope tight; state this limitation.
5. Each platform transaction has a unique `txn_id`; the bank reference is `bank_ref` which contains the txn_id in `utr`/`reference` field for most rows (mostly, not always: some rows need fallback matching).
6. Refunds are separate rows with `type=REFUND`, negative amount, and `original_txn_id`. Full refunds only.
7. Month-end cut is by SETTLEMENT date for bank and by TRANSACTION date for platform; the gap between those is the "timing difference" category.
8. Rounding tolerance per line = 0.01; any aggregate residual above tolerance after all line matching is reported.

## STEP 2: DATA GENERATOR (`generator.py`, seeded, deterministic)
Generate `platform_transactions.csv` (~1,000 rows: txn_id, created_at, amount, currency, type SALE/REFUND, original_txn_id, status) and `bank_settlements.csv` (settlement_id, bank_ref, settled_at, amount, batch_id). Many-to-one batching is NOT needed; keep 1 settlement per transaction.
~97% of rows are clean matches. PLANT exactly these gaps and write `data/ground_truth.json` listing each planted gap (type, ids, amount impact):
1. TIMING: 3-5 transactions dated Oct 29-31 that settled in Nov 1-2 (present in platform Oct, absent in bank Oct).
2. ROUNDING: ~200 lines where platform has 3-decimal amounts (e.g. 499.995) and bank rounded to 2 decimals so each line differs by <=0.005 (passes line tolerance) but the SUM differs by a visible amount (e.g. ~Rs 0.5-1.5). Per-line this is invisible; only aggregate shows it.
3. DUPLICATE: 1-2 duplicates in ONE dataset (e.g. same txn_id appearing twice in the bank file; also one platform duplicate with a different txn_id but identical amount/timestamp/customer, to test the fuzzy case).
4. ORPHAN REFUND: 1-2 refunds whose `original_txn_id` does not exist in the platform data (and optionally one whose original is in the previous month, tagged distinctly as "original in prior period, likely legitimate").
Also include 1-2 UNPLANTED-by-spec but realistic extras if cheap: a bank settlement with no platform txn (orphan settlement), and one amount mismatch beyond tolerance. List them in ground_truth as "bonus".

## STEP 3: RECONCILIATION ENGINE (`reconcile.py`)
Pure functions, fully unit-testable. Pipeline:
1. Validate/normalize input (Decimal parsing, UTC parsing, strip IDs, flag malformed rows instead of crashing).
2. Detect duplicates FIRST within each dataset (exact ID duplicates, and fuzzy duplicates = same amount + timestamp within 60s + same customer/merchant), remove from matching pool and report them.
3. Match in tiers: (a) exact txn_id/reference, (b) fallback amount + date window (+0 to +3 days) for rows with missing/garbled references, only when the candidate is unique; ambiguous candidates go to "needs review", never silently matched.
4. Classify every unmatched or mismatched item into exactly one category with a human-readable reason: TIMING_DIFFERENCE (settled next month), DUPLICATE (platform/bank), ORPHAN_REFUND (no original), ORPHAN_SETTLEMENT, AMOUNT_MISMATCH, ROUNDING_DRIFT, NEEDS_REVIEW.
5. Rounding: lines within tolerance count as matched, but compute the aggregate residual (sum platform - sum bank over matched lines) and report it as ROUNDING_DRIFT with count of lines and total.
6. Produce a **bridge/waterfall**: Platform total -> minus timing -> minus duplicates -> minus orphan refunds -> minus rounding drift -> ... = Bank total, with residual "unexplained" that must be 0.00 on generated data. This is the main answer to "why don't the books balance".
Idempotent, deterministic, O(n) via dict lookups.

## STEP 4: API + DASHBOARD
Endpoints: `POST /api/generate` (regenerate seed), `GET /api/reconcile`, `POST /api/reconcile/upload` (accept the two CSVs so it works on any data), `GET /api/export.csv` (exceptions list), `GET /health`.
Dashboard (one page, clean, readable): headline cards (platform total, bank total, difference, % matched), the bridge waterfall chart, a gap-category table with counts and amounts, a filterable exceptions table (id, category, amount, reason, suggested action), an "Assumptions" panel, and a "Ground truth check" badge showing planted gaps vs detected gaps (precision/recall) for the generated dataset. Handle empty/invalid upload with a clear error message.

## STEP 5: TESTS (`tests/`, document in TESTS.md)
- Unit: each gap type detected on a tiny hand-written fixture (5-10 rows each).
- Integration: generated dataset -> every planted gap in ground_truth.json found (recall 100%), no clean row falsely flagged (precision 100%), bridge residual == 0.00.
- Edge: empty files, header-only, malformed amount, negative sale, duplicate IDs in both files, same amount different ids (must NOT be a false duplicate if timestamps differ), month boundary at 23:59:59 UTC / 00:00:00, Decimal vs float trap (0.1+0.2 style), refund whose original is in the same file, ambiguous fallback match goes to NEEDS_REVIEW, re-running twice yields identical output.
- Property-style: shuffling row order never changes the result.
Run pytest at the end and paste real output into TESTS.md.

## STEP 6: DOCS
- README: what it does, how to run locally and via Docker, deployed URL placeholder, architecture in 6 lines.
- PRODUCTION_RISKS.md: exactly 3 sentences on what this would get wrong in production (e.g. fees/net settlement and many-to-one batch payouts, timezone/cutoff differences and FX, partial refunds/chargebacks/reversals, scale and streaming, no auth/audit trail).

## RULES
- No scope creep: no auth, no database, no frameworks beyond the stack. If tempted to add something, write it in PRODUCTION_RISKS.md instead.
- Never use floats for money. Never silently drop or auto-match ambiguous rows.
- After each step, run the tests and show me the result before continuing. If something fails, show the wrong turn and fix it (I'm submitting the full thread).
- At the end: give me the run commands, the deploy steps (Dockerfile ready for Render), and a 60-90 second demo script showing: generate data -> reconcile -> bridge -> click each gap -> ground-truth check -> upload bad file.