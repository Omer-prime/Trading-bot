from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.worker import Worker
from app.schemas.worker import (
    WorkerRuntimeEnabledFlags,
    WorkerRuntimeLifecycleFlags,
    WorkerRuntimeRead,
)
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


def _heartbeat_status(worker: Worker, *, stale_worker_ids: set[int]) -> str:
    if worker.heartbeat_at is None:
        return "missing"
    if worker.id in stale_worker_ids:
        return "stale"
    return "fresh"


def _runtime_lifecycle_flags(
    worker: Worker,
    *,
    heartbeat_status: str,
    can_fetch_runtime: bool,
) -> WorkerRuntimeLifecycleFlags:
    return WorkerRuntimeLifecycleFlags(
        worker_status=worker.status,
        is_active=worker.is_active,
        can_fetch_runtime=can_fetch_runtime,
        heartbeat_status=heartbeat_status,
        heartbeat_stale=heartbeat_status != "fresh",
        heartbeat_timeout_seconds=settings.worker_heartbeat_timeout_seconds,
    )


def _runtime_enabled_flags(worker: Worker) -> WorkerRuntimeEnabledFlags:
    return WorkerRuntimeEnabledFlags(
        worker_enabled=worker.status != WORKER_STATUS_DISABLED,
        account_enabled=worker.account.is_enabled,
        bot_config_present=worker.account.bot_config is not None,
    )


def get_worker_runtime_bundle(
    db: Session,
    *,
    worker_id: int,
    request: Request | None = None,
) -> WorkerRuntimeRead:
    now = utc_now()
    stale_workers = mark_stale_workers_offline(db, now=now)
    stale_worker_ids = {worker.id for worker in stale_workers}

    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        if stale_workers:
            db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    heartbeat_state = _heartbeat_status(worker, stale_worker_ids=stale_worker_ids)

    if worker.id in stale_worker_ids:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker heartbeat is stale; register again",
        )

    if worker.status == WORKER_STATUS_DISABLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is disabled",
        )
    if not worker.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is inactive; register again",
        )
    if worker.status == WORKER_STATUS_OFFLINE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is offline; heartbeat required",
        )
    if not worker.account.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account is disabled",
        )
    if not worker.account.bot_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot config not found for worker account",
        )

    lifecycle_flags = _runtime_lifecycle_flags(
        worker,
        heartbeat_status=heartbeat_state,
        can_fetch_runtime=True,
    )
    enabled_flags = _runtime_enabled_flags(worker)

    write_audit_log(
        db,
        actor_type="worker",
        actor_id=worker.id,
        action="worker.runtime_fetched",
        entity_type="worker",
        entity_id=worker.id,
        account_id=worker.account_id,
        payload_json={
            "account_id": worker.account_id,
            "lifecycle_flags": lifecycle_flags.model_dump(),
            "enabled_flags": enabled_flags.model_dump(),
        },
        request=request,
    )
    db.commit()
    db.refresh(worker)

    return WorkerRuntimeRead(
        worker=worker,
        account=worker.account,
        bot_config=worker.account.bot_config,
        lifecycle_flags=lifecycle_flags,
        enabled_flags=enabled_flags,
    )
