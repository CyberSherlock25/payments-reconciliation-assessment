from app.reconcile import reconcile


def p(txn, amount="10.000", when="2026-10-10T10:00:00Z", kind="SALE", original=""):
    return {"txn_id": txn, "created_at": when, "amount": amount, "currency": "INR",
            "type": kind, "original_txn_id": original, "status": "SUCCESS", "customer_id": txn}


def b(settlement, ref, amount="10.00", when="2026-10-11T10:00:00Z"):
    return {"settlement_id": settlement, "bank_ref": ref, "settled_at": when,
            "amount": amount, "batch_id": "b", "customer_id": ref.replace("utr:", "")}


def categories(result):
    return {row["category"] for row in result["categories"]}


def test_timing_and_orphan_settlement():
    result = reconcile([p("late", when="2026-10-31T23:59:59Z")],
                       [b("s", "utr:late", when="2026-11-01T00:00:00Z"), b("orphan", "utr:none")])
    assert "TIMING_DIFFERENCE" in categories(result)
    assert "ORPHAN_SETTLEMENT" in categories(result)


def test_orphan_refund_and_amount_mismatch():
    result = reconcile([p("r", "-10.000", kind="REFUND", original="missing"), p("x")],
                       [b("s", "utr:x", "20.00")])
    assert "ORPHAN_REFUND" in categories(result)
    assert "AMOUNT_MISMATCH" in categories(result)


def test_duplicate_and_ambiguous_fallback():
    rows = [p("a", "10.000", customer="a") if False else p("a", "10.000"),
            p("a", "10.000")]
    result = reconcile(rows, [b("s", "garbled", "10.00")])
    assert "DUPLICATE" in categories(result)


def test_malformed_and_order_independent():
    bad = p("bad", "not-money")
    one = reconcile([p("a")], [b("s", "utr:a")])
    two = reconcile([p("a")], [b("s", "utr:a")])
    malformed = reconcile([bad], [])
    assert one == two
    assert malformed["malformed_count"] == 1
def test_cumulative_rounding_difference():
    # Multiple individually small rounding differences
    # should produce a detectable aggregate difference.

    transactions = [
        p("r1", "10.004"),
        p("r2", "10.004"),
        p("r3", "10.004"),
    ]

    settlements = [
        b("s1", "utr:r1", "10.00"),
        b("s2", "utr:r2", "10.00"),
        b("s3", "utr:r3", "10.00"),
    ]

    result = reconcile(transactions, settlements)

    # Verify aggregate rounding difference.
    # Assertions must match your actual reconciliation output.