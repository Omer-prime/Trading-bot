import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("WORKER_SHARED_SECRET", "test-worker-secret")

API_ROOT = Path(__file__).resolve().parents[2] / "services" / "api"
sys.path.insert(0, str(API_ROOT))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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


def seed_account(
    db: Session,
    *,
    is_enabled: bool = True,
    with_config: bool = True,
) -> Account:
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

    if with_config:
        config = BotConfig(account_id=account.id)
        db.add(config)

    db.commit()
    db.refresh(account)
    return account


def audit_actions(db: Session) -> list[str]:
    return [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]
