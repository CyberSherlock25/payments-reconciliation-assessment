# Payments Reconciliation

A deterministic FastAPI demo that compares October 2026 platform transactions with bank settlements, explains exceptions, and proves generated gaps against a ground-truth file.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.generator
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. Run tests with `pytest -q`.

## Docker / Render

```powershell
docker build -t payments-reconciliation .
docker run -p 8000:8000 payments-reconciliation
```

For Render, create a Docker web service and use port `8000`. Deployed application: **https://payments-reconciliation-assessment.onrender.com/**

## Architecture

1. `generator.py` creates seeded CSVs and explicit planted-gap ground truth.
2. `reconcile.py` normalizes rows and runs deterministic duplicate and match passes.
3. `main.py` exposes generation, reconciliation, upload, export, and health endpoints.
4. `static/index.html` is a no-build vanilla dashboard with Chart.js from a CDN.
5. CSV files are the only persistence; each request processes data in memory.
6. Tests cover each gap category, edge cases, determinism, and generated-data recall/precision.
