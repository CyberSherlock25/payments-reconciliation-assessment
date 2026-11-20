from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.generator import DATA, generate
from app.reconcile import reconcile

app = FastAPI(title="Payments Reconciliation")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


def _read(name: str) -> list[dict[str, str]]:
    path = DATA / name
    if not path.exists():
        generate()
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run(platform: list[dict], bank: list[dict]) -> dict:
    result = reconcile(platform, bank)
    truth_path = DATA / "ground_truth.json"
    if truth_path.exists():
        truth = json.loads(truth_path.read_text(encoding="utf-8")).get("gaps", [])
        detected = {(item["category"], item["id"]) for item in result["exceptions"]}
        expected = {(gap["type"], gap["ids"][0]) for gap in truth}
        result["ground_truth"] = {"planted": len(expected), "detected": len(expected & detected),
                                  "recall_percent": round(100 * len(expected & detected) / max(len(expected), 1), 2),
                                  "precision_percent": round(100 * len(expected & detected) / max(len(detected), 1), 2)}
    return result


@app.get("/")
def home() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate")
def api_generate() -> dict:
    generate()
    return _run(_read("platform_transactions.csv"), _read("bank_settlements.csv"))


@app.get("/api/reconcile")
def api_reconcile() -> dict:
    return _run(_read("platform_transactions.csv"), _read("bank_settlements.csv"))


@app.post("/api/reconcile/upload")
async def upload(platform_file: Annotated[UploadFile, File()], bank_file: Annotated[UploadFile, File()]) -> JSONResponse:
    try:
        platform = list(csv.DictReader(io.StringIO((await platform_file.read()).decode("utf-8-sig"))))
        bank = list(csv.DictReader(io.StringIO((await bank_file.read()).decode("utf-8-sig"))))
        if not platform or not bank:
            raise ValueError("Both files must contain a header and at least one data row.")
        if "txn_id" not in platform[0] or "settlement_id" not in bank[0]:
            raise ValueError("Unexpected CSV headers.")
        return JSONResponse(_run(platform, bank))
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/export.csv")
def export_csv() -> StreamingResponse:
    rows = _run(_read("platform_transactions.csv"), _read("bank_settlements.csv"))["exceptions"]
    output = io.StringIO()
    fields = ["id", "category", "amount", "reason", "suggested_action", "dataset"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=exceptions.csv"})
