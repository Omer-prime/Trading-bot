from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.worker import Worker

from conftest import audit_actions, seed_account, worker_headers


def register_worker(client: TestClient, account_id: int) -> dict:
    response = client.post(
        "/api/v1/workers/register",
        headers=worker_headers(),
        json={"account_id": account_id, "machine_name": "runtime-box", "version": "1.0.0"},
    )
    assert response.status_code == 200
    return response.json()


def add_worker(
    db: Session,
    *,
    account_id: int,
    status: str = "online",
    is_active: bool = True,
    heartbeat_at=None,
) -> Worker:
    worker = Worker(
        account_id=account_id,
        machine_name="runtime-box",
        version="1.0.0",
        status=status,
        is_active=is_active,
        heartbeat_at=heartbeat_at or datetime.now(timezone.utc),
        last_started_at=datetime.now(timezone.utc),
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


def test_runtime_fetch_success_returns_deterministic_bundle(client: TestClient, db_session: Session):
    account = seed_account(db_session)
    worker = register_worker(client, account.id)

    response = client.get(
        f"/api/v1/workers/{worker['id']}/runtime",
        headers=worker_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "worker",
        "account",
        "bot_config",
        "lifecycle_flags",
        "enabled_flags",
    }
    assert payload["worker"]["id"] == worker["id"]
    assert payload["account"]["id"] == account.id
    assert payload["bot_config"]["account_id"] == account.id
    assert payload["lifecycle_flags"] == {
        "worker_status": "online",
        "is_active": True,
        "can_fetch_runtime": True,
        "heartbeat_status": "fresh",
        "heartbeat_stale": False,
        "heartbeat_timeout_seconds": 90,
    }
    assert payload["enabled_flags"] == {
        "worker_enabled": True,
        "account_enabled": True,
        "bot_config_present": True,
    }

    runtime_audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "worker.runtime_fetched")
        .one()
    )
    assert runtime_audit.payload_json["lifecycle_flags"]["can_fetch_runtime"] is True
    assert runtime_audit.payload_json["enabled_flags"]["bot_config_present"] is True


def test_runtime_fetch_rejects_invalid_secret(client: TestClient, db_session: Session):
    account = seed_account(db_session)
    worker = register_worker(client, account.id)

    response = client.get(
        f"/api/v1/workers/{worker['id']}/runtime",
        headers=worker_headers("wrong-secret"),
    )

    assert response.status_code == 401


def test_runtime_fetch_returns_404_for_missing_worker(client: TestClient):
    response = client.get("/api/v1/workers/999/runtime", headers=worker_headers())

    assert response.status_code == 404
    assert response.json()["detail"] == "Worker not found"


def test_runtime_fetch_rejects_disabled_worker(client: TestClient, db_session: Session):
    account = seed_account(db_session)
    worker = add_worker(
        db_session,
        account_id=account.id,
        status="disabled",
        is_active=False,
    )

    response = client.get(f"/api/v1/workers/{worker.id}/runtime", headers=worker_headers())

    assert response.status_code == 409
    assert response.json()["detail"] == "Worker is disabled"


def test_runtime_fetch_rejects_disabled_account(client: TestClient, db_session: Session):
    account = seed_account(db_session, is_enabled=False)
    worker = add_worker(db_session, account_id=account.id)

    response = client.get(f"/api/v1/workers/{worker.id}/runtime", headers=worker_headers())

    assert response.status_code == 409
    assert response.json()["detail"] == "Account is disabled"


def test_runtime_fetch_returns_clear_error_for_missing_config(client: TestClient, db_session: Session):
    account = seed_account(db_session, with_config=False)
    worker = add_worker(db_session, account_id=account.id)

    response = client.get(f"/api/v1/workers/{worker.id}/runtime", headers=worker_headers())

    assert response.status_code == 404
    assert response.json()["detail"] == "Bot config not found for worker account"


def test_runtime_fetch_marks_stale_worker_offline(client: TestClient, db_session: Session):
    account = seed_account(db_session)
    worker = add_worker(
        db_session,
        account_id=account.id,
        heartbeat_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )

    response = client.get(f"/api/v1/workers/{worker.id}/runtime", headers=worker_headers())

    assert response.status_code == 409
    assert response.json()["detail"] == "Worker heartbeat is stale; register again"

    db_session.refresh(worker)
    assert worker.status == "offline"
    assert worker.is_active is False
    assert "worker.heartbeat_timeout" in audit_actions(db_session)
    assert "worker.runtime_fetched" not in audit_actions(db_session)
