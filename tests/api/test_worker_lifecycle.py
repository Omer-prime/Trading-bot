import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("WORKER_SHARED_SECRET", "test-worker-secret")

API_ROOT = Path(__file__).resolve().parents[2] / "services" / "api"
sys.path.insert(0, str(API_ROOT))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.core.security import create_access_token
from app.main import app
from app.models.account import Account
from app.models.audit_log import AuditLog
from app.models.bot_config import BotConfig
from app.models.client import Client
from app.models.user import User
from app.models.worker import Worker


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session):
    settings.worker_shared_secret = "test-worker-secret"
    settings.worker_heartbeat_timeout_seconds = 90

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def worker_headers(secret: str = "test-worker-secret") -> dict[str, str]:
    return {"X-Worker-Secret": secret}


def admin_headers(db: Session) -> dict[str, str]:
    admin = User(
        email="admin@example.com",
        password_hash="unused",
        full_name="Admin",
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    token = create_access_token(subject=str(admin.id), extra_claims={"role": "admin"})
    return {"Authorization": f"Bearer {token}"}


def seed_account(db: Session, *, is_enabled: bool = True) -> Account:
    client = Client(name="Lifecycle Client", email="client@example.com")
    db.add(client)
    db.flush()

    account = Account(
        client_id=client.id,
        mt5_login=f"mt5-{datetime.now(timezone.utc).timestamp()}",
        server_name="Demo-Server",
        account_mode="monitor",
        symbol="XAUUSD",
        is_enabled=is_enabled,
    )
    db.add(account)
    db.flush()

    config = BotConfig(account_id=account.id)
    db.add(config)
    db.commit()
    db.refresh(account)
    return account


def audit_actions(db: Session) -> list[str]:
    return [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]


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
