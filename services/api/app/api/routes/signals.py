from fastapi import APIRouter, Depends, Request, status
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


@router.get("", response_model=list[SignalLogRead])
def list_signals(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(SignalLog).order_by(SignalLog.id.desc()).all()
