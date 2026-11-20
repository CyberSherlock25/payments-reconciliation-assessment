from decimal import Decimal

from app.reconcile import reconcile


def test_exact_match_uses_decimal():
    platform = [{
        "txn_id": "t1", "created_at": "2026-10-10T10:00:00Z",
        "amount": "0.300", "currency": "INR", "type": "SALE",
        "original_txn_id": "", "status": "SUCCESS", "customer_id": "c1",
    }]
    bank = [{
        "settlement_id": "s1", "bank_ref": "utr:t1",
        "settled_at": "2026-10-11T10:00:00Z", "amount": "0.30",
        "batch_id": "b1", "customer_id": "c1",
    }]
    result = reconcile(platform, bank)
    assert result["summary"]["matched_lines"] == 1
    assert result["summary"]["residual"] == "0.00"
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
