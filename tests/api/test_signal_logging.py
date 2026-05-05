from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.signal import SignalLog

from conftest import admin_headers, seed_account, worker_headers


def test_worker_can_persist_dry_run_signal(client: TestClient, db_session: Session):
    account = seed_account(db_session)

    response = client.post(
        "/api/v1/signals/dry-run",
        headers=worker_headers(),
        json={
            "account_id": account.id,
            "worker_id": 22,
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "timeframes_json": ["M5", "H1", "H4"],
            "direction": "buy",
            "trend_bias": "up",
            "liquidity_sweep_detected": True,
            "bos_detected": True,
            "entry_price": "2450.100000",
            "stop_loss": "2448.000000",
            "take_profit": "2454.300000",
            "rr_estimate": "2.0000",
            "status": "accepted",
            "payload_json": {"dry_run": True, "market_snapshot": {"M5": []}},
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["worker_id"] == 22
    assert payload["timeframes_json"] == ["M5", "H1", "H4"]
    assert payload["rr_estimate"] == "2.0000"

    signal = db_session.query(SignalLog).one()
    assert signal.account_id == account.id
    assert signal.symbol == "XAUUSD"
    assert signal.status == "accepted"
    assert signal.payload_json["market_snapshot"] == {"M5": []}


def test_admin_can_read_and_filter_dry_run_signals(client: TestClient, db_session: Session):
    account = seed_account(db_session)
    headers = worker_headers()
    accepted = {
        "account_id": account.id,
        "worker_id": 10,
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "timeframes_json": ["M5", "H1", "H4"],
        "direction": "buy",
        "trend_bias": "up",
        "status": "accepted",
        "payload_json": {"dry_run": True},
    }
    rejected = {
        "account_id": account.id,
        "worker_id": 11,
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "timeframes_json": ["M5", "H1", "H4"],
        "direction": "none",
        "trend_bias": "range",
        "status": "rejected",
        "rejection_reason": "trend filter blocked",
        "payload_json": {"dry_run": True},
    }
    accepted_response = client.post("/api/v1/signals/dry-run", headers=headers, json=accepted)
    rejected_response = client.post("/api/v1/signals/dry-run", headers=headers, json=rejected)
    assert accepted_response.status_code == 201
    assert rejected_response.status_code == 201

    admin = admin_headers(db_session)
    filtered = client.get(
        "/api/v1/signals/dry-run",
        headers=admin,
        params={
            "account_id": account.id,
            "worker_id": 11,
            "direction": "none",
            "status": "rejected",
            "rejection_reason": "trend filter blocked",
        },
    )
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()] == [rejected_response.json()["id"]]

    by_id = client.get(f"/api/v1/signals/dry-run/{accepted_response.json()['id']}", headers=admin)
    assert by_id.status_code == 200
    assert by_id.json()["status"] == "accepted"

    missing = client.get("/api/v1/signals/dry-run/9999", headers=admin)
    assert missing.status_code == 404


def test_signal_logging_rejects_invalid_worker_secret(client: TestClient, db_session: Session):
    account = seed_account(db_session)

    response = client.post(
        "/api/v1/signals/dry-run",
        headers=worker_headers("wrong-secret"),
        json={
            "account_id": account.id,
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "direction": "none",
            "status": "rejected",
            "rejection_reason": "trend filter blocked",
        },
    )

    assert response.status_code == 401
