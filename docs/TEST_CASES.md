
# ReconX — Test Cases

## Test Environment
- Application: ReconX
- Reporting Period: November 2026
- Currency: INR
- Testing Framework: Pytest
- Test Data: Synthetic CSV datasets

## TC-01: Normal Transaction Matching

Input:
A platform transaction has a matching bank settlement
with the same transaction reference and amount.

Expected Result:
Transaction should be classified as MATCHED.

Actual Result:
[Fill after running the test]

Status:
[PASS / FAIL]

## TC-02: Late Settlement

Input:
A November 30 transaction is settled on December 1.

Expected Result:
Transaction should be classified as LATE_SETTLEMENT
or next-month settlement.

Actual Result:
[Fill after running the test]

Status:
[PASS / FAIL]

## TC-03: Cumulative Rounding Difference

Input:
Multiple transactions have individual rounding
differences within the configured tolerance,
but their combined difference exceeds that tolerance.

Expected Result:
Individual differences and aggregate differences
should be reported accurately.

Actual Result:
[Fill after running the test]

Status:
[PASS / FAIL]

## TC-04: Duplicate Settlement

Input:
The bank settlement dataset contains a duplicate
settlement reference.

Expected Result:
Duplicate record should be identified and
must not be counted twice.

Actual Result:
[Fill after running the test]

Status:
[PASS / FAIL]

## TC-05: Orphan Refund

Input:
A refund references an original transaction
that does not exist in the platform dataset.

Expected Result:
Refund should be classified as ORPHAN_REFUND.

Actual Result:
[Fill after running the test]

Status:
[PASS / FAIL]

## TC-06: Missing Settlement

Input:
A platform transaction has no corresponding
bank settlement within the checked settlement window.

Expected Result:
Transaction should be flagged as missing or pending,
depending on the reporting cutoff and settlement window.

Actual Result:
[Fill after running the test]

Status:
[PASS / FAIL]

## TC-07: Invalid CSV

Input:
Upload a CSV file with missing required columns.

Expected Result:
Application should reject the file with a
clear validation message.

Actual Result:
[Fill after running the test]

Status:
[PASS / FAIL]
