from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.worker import Worker

from conftest import admin_headers, audit_actions, seed_account, worker_headers


def test_worker_register_reregister_duplicate_heartbeat_and_audit(client: TestClient, db_session: Session):
    account = seed_account(db_session)

    first_register = client.post(
        "/api/v1/workers/register",
        headers=worker_headers(),
        json={"account_id": account.id, "machine_name": "box-a", "version": "1.0.0"},
    )
    assert first_register.status_code == 200
    first_worker = first_register.json()
    assert first_worker["status"] == "online"
    assert first_worker["is_active"] is True

    reregister = client.post(
        "/api/v1/workers/register",
        headers=worker_headers(),
        json={"account_id": account.id, "machine_name": "box-a", "version": "1.0.1"},
    )
    assert reregister.status_code == 200
    assert reregister.json()["id"] == first_worker["id"]
    assert reregister.json()["version"] == "1.0.1"

    duplicate_register = client.post(
        "/api/v1/workers/register",
        headers=worker_headers(),
        json={"account_id": account.id, "machine_name": "box-b", "version": "1.0.0"},
    )
    assert duplicate_register.status_code == 200
    replacement_worker = duplicate_register.json()
    assert replacement_worker["id"] != first_worker["id"]
    assert replacement_worker["is_active"] is True

    retired_worker = db_session.get(Worker, first_worker["id"])
    assert retired_worker is not None
    assert retired_worker.status == "offline"
    assert retired_worker.is_active is False

    heartbeat = client.post(
        "/api/v1/workers/heartbeat",
        headers=worker_headers(),
        json={"worker_id": replacement_worker["id"], "status": "online"},
    )
    assert heartbeat.status_code == 200
    assert heartbeat.json()["status"] == "online"

    error_heartbeat = client.post(
        "/api/v1/workers/heartbeat",
        headers=worker_headers(),
        json={"worker_id": replacement_worker["id"], "status": "online", "last_error": "terminal disconnected"},
    )
    assert error_heartbeat.status_code == 200
    assert error_heartbeat.json()["status"] == "error"
    assert error_heartbeat.json()["last_error"] == "terminal disconnected"

    assert audit_actions(db_session) == [
        "worker.registered",
        "worker.re_registered",
        "worker.duplicate_retired",
        "worker.registered",
        "worker.heartbeat",
        "worker.heartbeat",
    ]


def test_worker_secret_and_disabled_rejections(client: TestClient, db_session: Session):
    account = seed_account(db_session)

    missing_secret = client.post(
        "/api/v1/workers/register",
        json={"account_id": account.id, "machine_name": "box-a"},
    )
    assert missing_secret.status_code == 401

    invalid_secret = client.post(
        "/api/v1/workers/register",
        headers=worker_headers("wrong-secret"),
        json={"account_id": account.id, "machine_name": "box-a"},
    )
    assert invalid_secret.status_code == 401

    disabled_account = seed_account(db_session, is_enabled=False)
    disabled_account_register = client.post(
        "/api/v1/workers/register",
        headers=worker_headers(),
        json={"account_id": disabled_account.id, "machine_name": "box-disabled"},
    )
    assert disabled_account_register.status_code == 409

    register = client.post(
        "/api/v1/workers/register",
        headers=worker_headers(),
        json={"account_id": account.id, "machine_name": "box-a"},
    )
    assert register.status_code == 200
    worker_id = register.json()["id"]

    disable_worker = client.patch(
        f"/api/v1/workers/{worker_id}/status",
        headers=admin_headers(db_session),
        json={"status": "disabled"},
    )
    assert disable_worker.status_code == 200
    assert disable_worker.json()["status"] == "disabled"
    assert disable_worker.json()["is_active"] is False

    disabled_worker_heartbeat = client.post(
        "/api/v1/workers/heartbeat",
        headers=worker_headers(),
        json={"worker_id": worker_id, "status": "online"},
    )
    assert disabled_worker_heartbeat.status_code == 409
    assert "inactive" in disabled_worker_heartbeat.json()["detail"]


def test_worker_timeout_marks_offline_and_audits(client: TestClient, db_session: Session):
    account = seed_account(db_session)
    stale_worker = Worker(
        account_id=account.id,
        machine_name="stale-box",
        version="1.0.0",
        status="online",
        is_active=True,
        heartbeat_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        last_started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    db_session.add(stale_worker)
    db_session.commit()
    db_session.refresh(stale_worker)

    list_workers = client.get("/api/v1/workers", headers=admin_headers(db_session))
    assert list_workers.status_code == 200

    db_session.refresh(stale_worker)
    assert stale_worker.status == "offline"
    assert stale_worker.is_active is False
    assert "worker.heartbeat_timeout" in audit_actions(db_session)
