from fastapi.testclient import TestClient

from app.main import app


def test_health_and_reconcile():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/api/reconcile")
    assert response.status_code == 200
    assert response.json()["bridge"][-1]["amount"] == "0.00"


def test_empty_upload_is_clear_error():
    client = TestClient(app)
    response = client.post("/api/reconcile/upload", files={
        "platform_file": ("platform.csv", b"txn_id,amount\n", "text/csv"),
        "bank_file": ("bank.csv", b"settlement_id,amount\n", "text/csv"),
    })
    assert response.status_code == 400
    assert "at least one data row" in response.json()["detail"]
