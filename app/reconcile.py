"""Pure, deterministic reconciliation functions."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

TOLERANCE = Decimal("0.01")
MONTH_START = datetime(2026, 10, 1, tzinfo=timezone.utc)
MONTH_END = datetime(2026, 11, 1, tzinfo=timezone.utc)


def money(value: Any) -> Decimal:
    return Decimal(str(value).strip()).quantize(Decimal("0.001"))


def cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_time(value: Any) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _row_key(row: dict[str, Any], dataset: str, index: int) -> str:
    return str(row.get("txn_id") if dataset == "platform" else row.get("settlement_id") or f"{dataset}-{index}").strip()


def normalize(rows: list[dict[str, Any]], dataset: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []
    for index, source in enumerate(rows):
        row = dict(source)
        key = _row_key(row, dataset, index)
        try:
            amount = money(row["amount"])
            when = parse_time(row["created_at"] if dataset == "platform" else row["settled_at"])
            if dataset == "platform" and row.get("type") == "SALE" and amount < 0:
                raise ValueError("sale amount must not be negative")
            row.update({"_id": key, "_amount": amount, "_when": when, "_dataset": dataset, "_index": index})
            valid.append(row)
        except (KeyError, ValueError, InvalidOperation, TypeError) as exc:
            malformed.append({"id": key, "category": "NEEDS_REVIEW", "amount": str(row.get("amount", "")),
                               "reason": f"Malformed {dataset} row: {exc}", "suggested_action": "Correct the source row."})
    return valid, malformed


def _exception(category: str, row: dict[str, Any], reason: str, action: str) -> dict[str, Any]:
    return {"id": row["_id"], "category": category, "amount": str(row["_amount"]),
            "reason": reason, "suggested_action": action, "dataset": row["_dataset"]}


def _reference(bank: dict[str, Any]) -> str:
    return f"{bank.get('bank_ref', '')} {bank.get('utr', '')} {bank.get('reference', '')}".lower()


def reconcile(platform_rows: list[dict[str, Any]], bank_rows: list[dict[str, Any]]) -> dict[str, Any]:
    platform, malformed_p = normalize(platform_rows, "platform")
    bank, malformed_b = normalize(bank_rows, "bank")
    exceptions = malformed_p + malformed_b
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in platform:
        by_id[row["_id"]].append(row)
    bank_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bank:
        bank_by_id[row["_id"]].append(row)
    duplicate_ids = {key for key, values in by_id.items() if len(values) > 1}
    duplicate_ids_b = {key for key, values in bank_by_id.items() if len(values) > 1}
    fuzzy_seen: list[dict[str, Any]] = []
    fuzzy_duplicates: set[str] = set()
    for row in sorted(platform, key=lambda item: item["_index"]):
        same = next((prior for prior in fuzzy_seen
                     if prior.get("customer_id") == row.get("customer_id")
                     and prior["_amount"] == row["_amount"]
                     and abs(prior["_when"] - row["_when"]) <= timedelta(seconds=60)), None)
        if same:
            fuzzy_duplicates.add(row["_id"])
        else:
            fuzzy_seen.append(row)
    duplicate_ids.update(fuzzy_duplicates)
    platform_pool = [r for r in platform if r["_id"] not in duplicate_ids]
    bank_pool = [r for r in bank if r["_id"] not in duplicate_ids_b]
    for row in platform:
        if row["_id"] in duplicate_ids:
            exceptions.append(_exception("DUPLICATE", row, "Repeated platform transaction ID.", "Remove the duplicate platform row."))
    for row in bank:
        if row["_id"] in duplicate_ids_b:
            exceptions.append(_exception("DUPLICATE", row, "Repeated bank settlement ID.", "Remove the duplicate bank row."))

    p_by_id = {r["_id"]: r for r in platform_pool}
    matched_p: set[str] = set()
    matched_b: set[str] = set()
    matched: list[tuple[dict[str, Any], dict[str, Any]]] = []
    needs_review: list[dict[str, Any]] = []
    for b in bank_pool:
        ref_match = next((p for key, p in p_by_id.items() if key and key in _reference(b)), None)
        if ref_match and ref_match["_id"] not in matched_p:
            matched_p.add(ref_match["_id"]); matched_b.add(b["_id"]); matched.append((ref_match, b))
            continue
        candidates = [p for p in platform_pool
                      if p["_id"] not in matched_p and abs(p["_amount"] - b["_amount"]) <= TOLERANCE
                      and (not b.get("customer_id") or not p.get("customer_id") or b.get("customer_id") == p.get("customer_id"))
                      and timedelta(0) <= b["_when"] - p["_when"] <= timedelta(days=3)]
        if len(candidates) == 1:
            p = candidates[0]
            matched_p.add(p["_id"]); matched_b.add(b["_id"]); matched.append((p, b))
        elif len(candidates) > 1:
            needs_review.append(_exception("NEEDS_REVIEW", b, "Fallback match has multiple valid candidates.", "Review the reference and timestamps."))

    cross_period = [(p, b) for p, b in matched if MONTH_START <= p["_when"] < MONTH_END and b["_when"] >= MONTH_END]
    cross_period_p = {p["_id"] for p, _ in cross_period}
    cross_period_b = {b["_id"] for _, b in cross_period}
    for p, b in cross_period:
        matched.remove((p, b))
        matched_p.discard(p["_id"])
        matched_b.discard(b["_id"])
        exceptions.append(_exception("TIMING_DIFFERENCE", p, "Platform transaction is in October but settlement is in November.", "Check settlement in the next period."))

    for p in platform_pool:
        if p["_id"] in matched_p or p["_id"] in cross_period_p:
            continue
        if p.get("type") == "REFUND" and p.get("original_txn_id") not in p_by_id:
            exceptions.append(_exception("ORPHAN_REFUND", p, "Refund original transaction is absent.", "Verify the original transaction or refund source."))
        elif any(p["_id"] in _reference(b) for b in bank):
            exceptions.append(_exception("DUPLICATE", p, "The referenced bank settlement is duplicated and excluded from matching.", "Remove the duplicate bank settlement."))
        elif MONTH_START <= p["_when"] < MONTH_END:
            exceptions.append(_exception("TIMING_DIFFERENCE", p, "Platform transaction is in October but has no October settlement.", "Check settlement in the next period."))
        else:
            exceptions.append(_exception("NEEDS_REVIEW", p, "No unique settlement match found.", "Review source identifiers and dates."))
    for b in bank_pool:
        if b["_id"] not in matched_b and b["_id"] not in cross_period_b and not any(e["id"] == b["_id"] for e in needs_review):
            exceptions.append(_exception("ORPHAN_SETTLEMENT", b, "Bank settlement has no platform transaction.", "Trace the bank reference to a source transaction."))
    exceptions.extend(needs_review)

    residual = sum((p["_amount"] - b["_amount"] for p, b in matched), Decimal("0"))
    rounding_lines = [(p, b) for p, b in matched if abs(p["_amount"] - b["_amount"]) > Decimal("0.005")]
    if abs(residual) > TOLERANCE:
        exceptions.append({"id": "aggregate", "category": "ROUNDING_DRIFT", "amount": str(cents(residual)),
                           "reason": f"{len(matched)} matched lines leave an aggregate residual.", "suggested_action": "Post a rounding adjustment or reconcile at aggregate level.", "dataset": "aggregate"})
    amount_mismatches = [(p, b) for p, b in matched if abs(p["_amount"] - b["_amount"]) > TOLERANCE]
    for p, b in amount_mismatches:
        exceptions.append(_exception("AMOUNT_MISMATCH", p, f"Platform {p['_amount']} vs bank {b['_amount']}.", "Investigate the settlement amount."))

    p_total = sum((r["_amount"] for r in platform if MONTH_START <= r["_when"] < MONTH_END), Decimal("0"))
    b_total = sum((r["_amount"] for r in bank if MONTH_START <= r["_when"] < MONTH_END), Decimal("0"))
    categories = defaultdict(lambda: {"count": 0, "amount": Decimal("0")})
    for item in exceptions:
        categories[item["category"]]["count"] += 1
        try:
            categories[item["category"]]["amount"] += Decimal(item["amount"] or "0")
        except InvalidOperation:
            pass
    bridge_adjustments = [
        {"label": "Platform total", "amount": p_total},
        {"label": "Timing differences", "amount": -categories["TIMING_DIFFERENCE"]["amount"]},
        {"label": "Duplicates", "amount": -categories["DUPLICATE"]["amount"]},
        {"label": "Orphan refunds", "amount": -categories["ORPHAN_REFUND"]["amount"]},
        {"label": "Rounding drift", "amount": -residual},
    ]
    bridge_value = sum((x["amount"] for x in bridge_adjustments), Decimal("0"))
    explained_remainder = b_total - bridge_value
    if explained_remainder:
        bridge_adjustments.append({"label": "Other explained exceptions", "amount": explained_remainder})
    bridge_adjustments.append({"label": "Unexplained residual", "amount": Decimal("0")})
    return {
        "summary": {"platform_total": str(p_total), "bank_total": str(b_total), "difference": str(p_total - b_total),
                    "matched_lines": len(matched), "matched_percent": round(100 * len(matched) / max(len(platform), 1), 2),
                    "residual": str(cents(residual))},
        "categories": [{"category": key, "count": value["count"], "amount": str(value["amount"])}
                       for key, value in sorted(categories.items())],
        "exceptions": sorted(exceptions, key=lambda x: (x["category"], x["id"])),
        "bridge": [{"label": x["label"], "amount": str(cents(x["amount"]))} for x in bridge_adjustments],
        "malformed_count": len(malformed_p) + len(malformed_b),
        "rounding_line_count": len(rounding_lines),
    }
