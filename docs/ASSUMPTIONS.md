# Assumptions

- Currency is INR and the reconciliation month is October 2026.
- All timestamps are UTC; the bank cutoff is also UTC. An IST/UTC boundary can change month-end classification in production.
- Platform amounts have three decimal places. Bank amounts are rounded half-up to two decimals per line.
- Settlement lag is one to two calendar days; weekends push settlement to the next business day.
- Settlements are gross of fees. Fees are intentionally ignored in this assessment.
- Platform `txn_id` values are unique in clean data. Bank `bank_ref` usually contains the transaction ID in `utr` or `reference`, but fallback matching handles missing or garbled references.
- Refunds are separate negative rows with `type=REFUND` and `original_txn_id`; only full refunds are modeled.
- The month-end cut uses platform transaction date and bank settlement date. A cross-month item is a `TIMING_DIFFERENCE`.
- Per-line rounding tolerance is INR 0.01. Any aggregate residual over that tolerance after line matching is `ROUNDING_DRIFT`.

