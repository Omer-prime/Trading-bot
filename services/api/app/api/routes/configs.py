from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.account import Account
from app.models.bot_config import BotConfig
from app.models.user import User
from app.schemas.bot_config import BotConfigCreate, BotConfigRead, BotConfigUpdate
from app.services.audit import write_audit_log

router = APIRouter(
    prefix="/configs",
    tags=["configs"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[BotConfigRead])
def list_configs(db: Session = Depends(get_db)):
    return db.query(BotConfig).order_by(BotConfig.id.desc()).all()


@router.get("/{config_id}", response_model=BotConfigRead)
def get_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(BotConfig).filter(BotConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot config not found",
        )
    return config


@router.post("", response_model=BotConfigRead, status_code=status.HTTP_201_CREATED)
def create_config(
    payload: BotConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    account = db.query(Account).filter(Account.id == payload.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    existing_config = (
        db.query(BotConfig)
        .filter(BotConfig.account_id == payload.account_id)
        .first()
    )
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot config already exists for this account",
        )

    config = BotConfig(**payload.model_dump())

    try:
        db.add(config)
        db.flush()
        write_audit_log(
            db,
            actor_type="user",
            actor_id=current_user.id,
            action="config.created",
            entity_type="bot_config",
            entity_id=config.id,
            account_id=config.account_id,
            payload_json=payload.model_dump(),
            request=request,
        )
        db.commit()
        db.refresh(config)
        return config
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create bot config",
        )


@router.patch("/{config_id}", response_model=BotConfigRead)
def update_config(
    config_id: int,
    payload: BotConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    config = db.query(BotConfig).filter(BotConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot config not found",
        )

    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(config, key, value)

    try:
        write_audit_log(
            db,
            actor_type="user",
            actor_id=current_user.id,
            action="config.updated",
            entity_type="bot_config",
            entity_id=config.id,
            account_id=config.account_id,
            payload_json=changes,
            request=request,
        )
        db.commit()
        db.refresh(config)
        return config
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update bot config",
        )
