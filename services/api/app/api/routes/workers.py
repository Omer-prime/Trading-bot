from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin, verify_worker_secret
from app.core.database import get_db
from app.models.worker import Worker
from app.models.account import Account
from app.models.user import User
from app.schemas.worker import WorkerHeartbeatRequest, WorkerRead, WorkerRegisterRequest, WorkerStatusUpdate
from app.schemas.worker import WorkerRuntimeRead
from app.services.audit import write_audit_log
from app.services.workers import (
    WORKER_STATUS_ERROR,
    WORKER_STATUS_DISABLED,
    WORKER_STATUS_OFFLINE,
    WORKER_STATUS_ONLINE,
    mark_stale_workers_offline,
    retire_duplicate_workers,
    utc_now,
)

router = APIRouter(prefix="/workers", tags=["workers"])


@router.post("/register", response_model=WorkerRead, dependencies=[Depends(verify_worker_secret)])
def register_worker(
    payload: WorkerRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    now = utc_now()
    mark_stale_workers_offline(db, now=now)

    account = db.query(Account).filter(Account.id == payload.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not account.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account is disabled",
        )

    existing_worker_query = db.query(Worker).filter(
        Worker.account_id == payload.account_id,
        Worker.machine_name == payload.machine_name,
    )
    worker = existing_worker_query.order_by(Worker.id.desc()).first()
    action = "worker.registered"

    if worker:
        if worker.status == WORKER_STATUS_DISABLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Worker is disabled",
            )
        action = "worker.re_registered"
        worker.version = payload.version
        worker.status = WORKER_STATUS_ONLINE
        worker.is_active = True
        worker.heartbeat_at = now
        worker.last_started_at = now
        worker.last_error = None
        worker.last_error_at = None
    else:
        worker = Worker(
            account_id=payload.account_id,
            machine_name=payload.machine_name,
            version=payload.version,
            status=WORKER_STATUS_ONLINE,
            is_active=True,
            heartbeat_at=now,
            last_started_at=now,
        )
        db.add(worker)

    db.flush()
    retire_duplicate_workers(
        db,
        account_id=payload.account_id,
        keep_worker_id=worker.id,
    )
    write_audit_log(
        db,
        actor_type="worker",
        actor_id=worker.id,
        action=action,
        entity_type="worker",
        entity_id=worker.id,
        account_id=worker.account_id,
        payload_json=payload.model_dump(),
        request=request,
    )
    db.commit()
    db.refresh(worker)
    return worker


@router.post("/heartbeat", response_model=WorkerRead, dependencies=[Depends(verify_worker_secret)])
def worker_heartbeat(
    payload: WorkerHeartbeatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    now = utc_now()
    mark_stale_workers_offline(db, now=now)

    worker = db.query(Worker).filter(Worker.id == payload.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if not worker.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is inactive; register again",
        )
    if worker.status == WORKER_STATUS_DISABLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is disabled",
        )

    worker.status = payload.status
    worker.heartbeat_at = now

    if payload.last_error:
        worker.last_error = payload.last_error
        worker.last_error_at = now
        worker.status = WORKER_STATUS_ERROR
    elif payload.status == WORKER_STATUS_DISABLED:
        worker.is_active = False
    elif payload.status != WORKER_STATUS_ERROR:
        worker.last_error = None
        worker.last_error_at = None

    write_audit_log(
        db,
        actor_type="worker",
        actor_id=worker.id,
        action="worker.heartbeat",
        entity_type="worker",
        entity_id=worker.id,
        account_id=worker.account_id,
        payload_json=payload.model_dump(),
        request=request,
    )
    db.commit()
    db.refresh(worker)
    return worker


@router.patch("/{worker_id}/status", response_model=WorkerRead)
def update_worker_status(
    worker_id: int,
    payload: WorkerStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.status = payload.status
    if payload.status in {WORKER_STATUS_DISABLED, WORKER_STATUS_OFFLINE}:
        worker.is_active = False

    if payload.is_active is not None:
        worker.is_active = payload.is_active

    if payload.last_error is not None:
        worker.last_error = payload.last_error
        worker.last_error_at = utc_now()
        worker.status = WORKER_STATUS_ERROR

    write_audit_log(
        db,
        actor_type="user",
        actor_id=current_user.id,
        action="worker.status_updated",
        entity_type="worker",
        entity_id=worker.id,
        account_id=worker.account_id,
        payload_json=payload.model_dump(),
        request=request,
    )

    db.commit()
    db.refresh(worker)
    return worker


@router.get("", response_model=list[WorkerRead])
def list_workers(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    stale_workers = mark_stale_workers_offline(db)
    if stale_workers:
        db.commit()
    return db.query(Worker).order_by(Worker.id.desc()).all()


@router.get("/{worker_id}", response_model=WorkerRead)
def get_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    stale_workers = mark_stale_workers_offline(db)
    if stale_workers:
        db.commit()
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@router.get("/{worker_id}/runtime", response_model=WorkerRuntimeRead, dependencies=[Depends(verify_worker_secret)])
def get_worker_runtime(
    worker_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    now = utc_now()
    mark_stale_workers_offline(db, now=now)

    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if not worker.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is inactive; register again",
        )
    if worker.status == WORKER_STATUS_DISABLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is disabled",
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

    write_audit_log(
        db,
        actor_type="worker",
        actor_id=worker.id,
        action="worker.runtime_fetched",
        entity_type="worker",
        entity_id=worker.id,
        account_id=worker.account_id,
        payload_json={"account_id": worker.account_id},
        request=request,
    )
    db.commit()
    db.refresh(worker)

    return WorkerRuntimeRead(
        worker=worker,
        account=worker.account,
        config=worker.account.bot_config,
    )
