"""Seeded assessment data generator."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def generate(seed: int = 202610) -> dict:
    rng = Random(seed)
    start = datetime(2026, 10, 1, 8, tzinfo=timezone.utc)
    platform: list[dict] = []
    bank: list[dict] = []
    truth: list[dict] = []
    for i in range(1000):
        created = start + timedelta(minutes=i * 37)
        amount = Decimal(100 + (i % 19) * 25) + (Decimal("0.995") if i < 200 else Decimal("0.000"))
        row = {"txn_id": f"txn_{i:04d}", "created_at": _iso(created), "amount": f"{amount:.3f}",
               "currency": "INR", "type": "SALE", "original_txn_id": "", "status": "SUCCESS",
               "customer_id": f"customer_{i:04d}"}
        platform.append(row)
        settled = created + timedelta(days=1 if created.weekday() < 4 else 3)
        bank.append({"settlement_id": f"set_{i:04d}", "bank_ref": f"utr:{row['txn_id']}",
                     "settled_at": _iso(settled), "amount": f"{amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}",
                     "batch_id": f"batch_{settled.date()}", "customer_id": row["customer_id"]})
    truth.append({"type": "ROUNDING_DRIFT", "ids": ["aggregate"], "amount": "-1.00"})

    timing_ids = ["txn_0996", "txn_0997", "txn_0998", "txn_0999"]
    for index in range(996, 1000):
        date = datetime(2026, 10, 29 + (index - 996) // 2, 12, tzinfo=timezone.utc)
        platform[index]["created_at"] = _iso(date)
        bank[index]["settled_at"] = _iso(datetime(2026, 11, 1 + (index - 996) // 2, 10, tzinfo=timezone.utc))
    truth.extend({"type": "TIMING_DIFFERENCE", "ids": [key], "amount": platform[int(key.split("_")[1])]["amount"]} for key in timing_ids)
    bank[10]["bank_ref"] = "garbled"
    bank[10]["settled_at"] = _iso(datetime.fromisoformat(platform[10]["created_at"].replace("Z", "+00:00")) + timedelta(days=1))
    bank[10]["amount"] = f"{Decimal(platform[10]['amount']):.2f}"
    bank.append(dict(bank[20], settlement_id="set_duplicate", bank_ref=f"utr:{platform[20]['txn_id']}"))
    bank[20]["settlement_id"] = "set_duplicate"
    truth.append({"type": "DUPLICATE", "ids": ["set_duplicate"], "amount": bank[20]["amount"]})
    platform.append({"txn_id": "txn_duplicate", "created_at": platform[21]["created_at"], "amount": platform[21]["amount"],
                     "currency": "INR", "type": "SALE", "original_txn_id": "", "status": "SUCCESS",
                     "customer_id": platform[21]["customer_id"]})
    truth.append({"type": "DUPLICATE", "ids": ["txn_duplicate"], "amount": platform[21]["amount"]})
    refund = {"txn_id": "refund_orphan", "created_at": _iso(datetime(2026, 10, 20, tzinfo=timezone.utc)),
              "amount": "-75.000", "currency": "INR", "type": "REFUND", "original_txn_id": "missing_original",
              "status": "SUCCESS", "customer_id": "customer_refund"}
    platform.append(refund)
    truth.append({"type": "ORPHAN_REFUND", "ids": ["refund_orphan"], "amount": refund["amount"]})
    bank.append({"settlement_id": "orphan_settlement", "bank_ref": "utr:unknown", "settled_at": "2026-10-20T12:00:00Z",
                 "amount": "123.45", "batch_id": "batch_orphan", "customer_id": "unknown"})
    truth.append({"type": "ORPHAN_SETTLEMENT", "ids": ["orphan_settlement"], "amount": "123.45"})
    bank[30]["amount"] = f"{Decimal(bank[30]['amount']) + Decimal('5.00'):.2f}"
    truth.append({"type": "AMOUNT_MISMATCH", "ids": ["txn_0030"], "amount": "5.00"})
    DATA.mkdir(exist_ok=True)
    for filename, rows in (("platform_transactions.csv", platform), ("bank_settlements.csv", bank)):
        with (DATA / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    (DATA / "ground_truth.json").write_text(json.dumps({"seed": seed, "gaps": truth}, indent=2), encoding="utf-8")
    return {"platform": platform, "bank": bank, "ground_truth": truth}


if __name__ == "__main__":
    generate()
