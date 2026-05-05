from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.signal import SignalLog

from conftest import seed_account, worker_headers


def test_worker_can_persist_dry_run_signal(client: TestClient, db_session: Session):
    account = seed_account(db_session)

    response = client.post(
        "/api/v1/signals/dry-run",
        headers=worker_headers(),
        json={
            "account_id": account.id,
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "direction": "buy",
            "trend_bias": "up",
            "liquidity_sweep_detected": True,
            "bos_detected": True,
            "entry_price": "2450.100000",
            "stop_loss": "2448.000000",
            "take_profit": "2454.300000",
            "rr_estimate": "2.0000",
            "status": "accepted",
            "payload_json": {"dry_run": True},
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["rr_estimate"] == "2.0000"

    signal = db_session.query(SignalLog).one()
    assert signal.account_id == account.id
    assert signal.symbol == "XAUUSD"
    assert signal.status == "accepted"


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
