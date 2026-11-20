# Tests

The suite covers Decimal exact matching, timing differences, orphan refunds and settlements, duplicates, amount mismatches, malformed rows, empty/header-only uploads, API health/reconcile behavior, generated ground truth, and deterministic reruns.

The final local run was:

```text
.......                                                                  [100%]
============================== warnings summary ===============================
7 passed, 22 warnings in 0.57s
```

The warnings are dependency deprecations from the installed Python 3.15 environment; the Dockerfile targets Python 3.11 as required.

Generated-data verification was also run:

```text
planted 10 detected 10 missing [] bridge_residual 0.00
```

