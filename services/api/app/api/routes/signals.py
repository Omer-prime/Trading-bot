from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin, verify_worker_secret
from app.core.database import get_db
from app.models.signal import SignalLog
from app.models.user import User
from app.schemas.signal import DryRunSignalCreate, SignalLogRead
from app.services.audit import write_audit_log

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/dry-run", response_model=SignalLogRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_worker_secret)])
def create_dry_run_signal(
    payload: DryRunSignalCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    signal = SignalLog(**payload.model_dump())
    db.add(signal)
    db.flush()

    write_audit_log(
        db,
        actor_type="worker",
        action="signal.dry_run_logged",
        entity_type="signal",
        entity_id=signal.id,
        account_id=signal.account_id,
        payload_json=payload.model_dump(mode="json"),
        request=request,
    )
    db.commit()
    db.refresh(signal)
    return signal


@router.get("/dry-run", response_model=list[SignalLogRead])
def list_dry_run_signals(
    account_id: int | None = None,
    worker_id: int | None = None,
    direction: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    rejection_reason: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(SignalLog)

    if account_id is not None:
        query = query.filter(SignalLog.account_id == account_id)
    if worker_id is not None:
        query = query.filter(SignalLog.worker_id == worker_id)
    if direction is not None:
        query = query.filter(SignalLog.direction == direction)
    if status_filter is not None:
        query = query.filter(SignalLog.status == status_filter)
    if rejection_reason is not None:
        query = query.filter(SignalLog.rejection_reason == rejection_reason)

    return query.order_by(SignalLog.id.desc()).all()


@router.get("/dry-run/{signal_id}", response_model=SignalLogRead)
def get_dry_run_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    signal = db.query(SignalLog).filter(SignalLog.id == signal_id).first()
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dry-run signal not found",
        )
    return signal


@router.get("", response_model=list[SignalLogRead])
def list_signals(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(SignalLog).order_by(SignalLog.id.desc()).all()
