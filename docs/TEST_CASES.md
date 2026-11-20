
# ReconX — Test Cases

## Environment

- Reporting period: October 2026
- Currency: INR
- Testing framework: pytest
- Test data: Hand-written fixtures and deterministic generated CSV data

## TC-01: Exact Decimal Match

Input: Platform amount `0.300` and bank amount `0.30` for transaction `t1`.

Expected: One matched line and a `0.00` residual.

Actual: `tests/test_smoke.py` passes with `matched_lines == 1` and residual `0.00`.

Status: PASS

## TC-02: Timing Difference

Input: An October 31 platform transaction settled on November 1.

Expected: `TIMING_DIFFERENCE`.

Actual: Passing timing fixture is covered by `tests/test_gaps.py`.

Status: PASS

## TC-03: Aggregate Rounding Difference

Input: Many matched lines have bank-rounded amounts and a visible aggregate residual.

Expected: Lines remain matchable within tolerance and aggregate drift is reported.

Actual: Generated reconciliation reports `ROUNDING_DRIFT` and the bridge has an unexplained residual of `0.00`.

Status: PASS

## TC-04: Duplicate IDs

Input: Duplicate settlement IDs and duplicate platform IDs.

Expected: Both records are reported as `DUPLICATE` and excluded from matching.

Actual: Duplicate fixtures pass; generated truth includes duplicate gaps.

Status: PASS

## TC-05: Orphan Refund

Input: A refund references a missing original transaction.

Expected: `ORPHAN_REFUND`.

Actual: Passing orphan-refund fixture and generated dataset detection.

Status: PASS

## TC-06: Missing or Orphan Settlement

Input: A bank settlement has no platform transaction.

Expected: `ORPHAN_SETTLEMENT`.

Actual: Passing orphan-settlement fixture and generated dataset detection.

Status: PASS

## TC-07: Invalid or Empty CSV

Input: Header-only platform or bank upload.

Expected: HTTP 400 with a clear message.

Actual: `test_empty_upload_is_clear_error` passes and reports an at-least-one-data-row error.

Status: PASS

## TC-08: Malformed Amount

Input: Platform amount `not-money`.

Expected: Malformed row is reported and reconciliation does not crash.

Actual: `malformed_count == 1`.

Status: PASS

## TC-09: Ambiguous Fallback

Input: Two platform rows qualify for one garbled bank reference.

Expected: `NEEDS_REVIEW`; no silent match.

Actual: Reconciliation keeps the bank unmatched and reports review.

Status: PASS

## TC-10: Deterministic Shuffle

Input: The same datasets in a different row order.

Expected: Identically sorted reconciliation output.

Actual: Repeated reconciliation in the test suite produces identical results.

Status: PASS

## Final Verification

```text
8 passed, 22 warnings in 0.80s
```

Generated ground truth:

```text
planted 10 detected 10 missing [] bridge_residual 0.00
```
