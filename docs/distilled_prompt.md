
# ReconX — Payment Reconciliation System
## Distilled Project Prompt

### 1. Project Overview

Project Name: ReconX

ReconX is a Payment Reconciliation System designed to identify discrepancies between payment transactions recorded by a payment platform and settlement records reported by a bank.

The main objective is to investigate why a company's financial books do not balance at the end of a reporting month and clearly identify the reasons behind every mismatch.

### 2. Problem Statement

A payment platform records transactions immediately when customers make payments. However, banks process payments in batches and generally settle funds 1–2 days later.

At the end of each month, the platform's transaction records and bank settlement records should reconcile.

ReconX must compare both datasets, identify discrepancies, calculate financial differences, and provide clear explanations for the gaps.

### 3. Core Objectives

- Compare platform transaction records with bank settlement records.
- Identify matched and unmatched transactions.
- Detect missing and delayed settlements.
- Identify duplicate entries.
- Detect rounding differences that become visible when amounts are aggregated.
- Identify refunds without matching original transactions.
- Calculate total transaction and settlement amounts.
- Explain why the financial records do not balance.
- Generate clear reconciliation reports.

### 4. Required Discrepancy Scenarios

The system must successfully identify all four scenarios specified in the assessment.

**1. Late Settlement**
- A transaction is recorded during November.
- Its corresponding bank settlement occurs in December.
- The system must identify it as a next-month settlement.
- It must not incorrectly classify it as permanently missing.

**2. Cumulative Rounding Difference**
- Introduce small rounding differences across multiple transactions.
- Individual differences should remain within the defined tolerance.
- When all differences are summed, the aggregate difference should become noticeable.
- The system must identify and report the cumulative financial difference.

**3. Duplicate Entry**
- Introduce a duplicate record in one of the datasets.
- The system must identify duplicate transaction or settlement references.
- Duplicate amounts must not be incorrectly counted twice in the reconciliation totals.
- Duplicate records must remain visible in the discrepancy report.

**4. Orphan Refund**
- Introduce a refund referencing an original transaction ID that does not exist.
- The system must identify the invalid reference.
- Classify the record as an ORPHAN_REFUND.
- Display the refund amount and relevant reference information.

### 5. Dataset Requirements

Generate synthetic datasets because no test files are provided in the assessment.

The datasets must contain:
- Normal successful transactions.
- Corresponding bank settlements.
- A next-month settlement.
- Multiple small rounding differences.
- At least one duplicate entry.
- At least one orphan refund.

Both datasets must contain realistic and consistent records except for the deliberately introduced discrepancies.

### 6. Business Assumptions

- The reporting period is November 2026.
- The reporting currency is INR.
- Platform transactions are recorded immediately.
- Bank settlements generally occur 1–2 days later.
- Transaction references are used for matching.
- Monetary calculations must use accurate decimal arithmetic.
- Rounding tolerance must be documented.
- Duplicate records must not be counted twice.
- Refunds must reference valid original transactions.
- Transactions settled in the following month must be reported separately.
- Every discrepancy must have an understandable explanation.

All assumptions should be documented and clearly communicated.

### 7. Functional Requirements

The application should provide:

1. Transaction dataset management.
2. Bank settlement dataset management.
3. CSV upload and validation.
4. Automated transaction matching.
5. Discrepancy detection.
6. Late settlement identification.
7. Duplicate entry detection.
8. Individual and cumulative rounding analysis.
9. Orphan refund detection.
10. Reconciliation summary.
11. Financial difference calculations.
12. Detailed discrepancy reports.
13. Exportable reconciliation results.

### 8. Technical Requirements

Use the existing project's actual technology stack and architecture.

The implementation should prioritize:
- Modular and maintainable code.
- Accurate financial calculations.
- Reliable data processing.
- Proper input validation.
- Clear API responses.
- Explainable reconciliation logic.
- Responsive user interface.
- Automated testing.

Do not introduce unnecessary technologies or rewrite working components without a valid reason.

### 9. Testing Requirements

Create test cases to verify:

- Normal transaction matching.
- Next-month settlement detection.
- Cumulative rounding difference detection.
- Duplicate entry identification.
- Orphan refund identification.
- Missing settlement detection.
- Invalid CSV handling.

Each test must include input conditions, expected output, actual output, and PASS/FAIL status.

### 10. Expected Application Output

The application should clearly display:

- Total platform transactions.
- Total bank settlements.
- Matched transactions.
- Unmatched transactions.
- Delayed settlements.
- Duplicate entries.
- Rounding differences.
- Orphan refunds.
- Overall reconciliation difference.

Every discrepancy should include its category, relevant reference, amount, and explanation.

### 11. Quality and Reliability

- Use accurate monetary calculations.
- Avoid silently ignoring discrepancies.
- Handle invalid and missing data safely.
- Maintain consistency between dashboard totals and reconciliation reports.
- Ensure that the four required scenarios can be demonstrated using the generated datasets.
- Provide meaningful error messages.

### 12. Final Assessment Deliverables

Prepare the following five deliverables:

1. Brainstorming Thread:
   Complete original LLM conversation without cleaning or modifying it.

2. Distilled Prompt and Raw Prompt:
   A consolidated project specification and the actual original prompt used with the AI coding tool.

3. AI Coding Execution Thread:
   Complete GitHub Copilot or other AI coding tool conversation, including errors, corrections, and wrong turns.

4. Test Cases:
   Automated and manual test cases with actual results.

5. Working Output:
   - Deployed application link.
   - Complete source code ZIP.
   - Application demonstration video.
   - Three sentences describing what the application could get wrong in production.

### 13. Final Goal

Build a reliable, explainable, and working Payment Reconciliation System that demonstrates how financial discrepancies can be identified, investigated, classified, and reported.

The application must demonstrate all four assessment-required discrepancy scenarios and clearly explain why the payment platform's books and bank settlement records do not balance.
