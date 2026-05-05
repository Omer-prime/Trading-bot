from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.worker import Worker
from app.services.audit import write_audit_log

WORKER_STATUS_ONLINE = "online"
WORKER_STATUS_OFFLINE = "offline"
WORKER_STATUS_ERROR = "error"
WORKER_STATUS_DISABLED = "disabled"
WORKER_STATUSES = {
    WORKER_STATUS_ONLINE,
    WORKER_STATUS_OFFLINE,
    WORKER_STATUS_ERROR,
    WORKER_STATUS_DISABLED,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def mark_stale_workers_offline(db: Session, *, now: datetime | None = None) -> list[Worker]:
    checked_at = now or utc_now()
    cutoff = checked_at - timedelta(seconds=settings.worker_heartbeat_timeout_seconds)
    stale_workers = (
        db.query(Worker)
        .filter(
            Worker.is_active.is_(True),
            Worker.status == WORKER_STATUS_ONLINE,
            Worker.heartbeat_at.isnot(None),
            Worker.heartbeat_at < cutoff,
        )
        .all()
    )

    for worker in stale_workers:
        worker.status = WORKER_STATUS_OFFLINE
        worker.is_active = False
        write_audit_log(
            db,
            actor_type="system",
            action="worker.heartbeat_timeout",
            entity_type="worker",
            entity_id=worker.id,
            account_id=worker.account_id,
            payload_json={
                "heartbeat_at": worker.heartbeat_at.isoformat() if worker.heartbeat_at else None,
                "timeout_seconds": settings.worker_heartbeat_timeout_seconds,
            },
        )

    return stale_workers


def retire_duplicate_workers(
    db: Session,
    *,
    account_id: int,
    keep_worker_id: int | None,
) -> list[Worker]:
    query = db.query(Worker).filter(
        Worker.account_id == account_id,
        Worker.is_active.is_(True),
    )
    if keep_worker_id is not None:
        query = query.filter(Worker.id != keep_worker_id)

    duplicate_workers = query.all()
    for worker in duplicate_workers:
        worker.status = WORKER_STATUS_OFFLINE
        worker.is_active = False
        write_audit_log(
            db,
            actor_type="system",
            action="worker.duplicate_retired",
            entity_type="worker",
            entity_id=worker.id,
            account_id=worker.account_id,
            payload_json={"replacement_worker_id": keep_worker_id},
        )

    return duplicate_workers
