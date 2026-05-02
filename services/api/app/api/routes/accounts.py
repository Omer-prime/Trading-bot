from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.account import Account
from app.models.client import Client
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.services.audit import write_audit_log

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.id.desc()).all()


@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    client = db.query(Client).filter(Client.id == payload.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    existing_account = (
        db.query(Account)
        .filter(Account.mt5_login == payload.mt5_login)
        .first()
    )
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MT5 login already exists",
        )

    account = Account(**payload.model_dump())

    try:
        db.add(account)
        db.flush()
        write_audit_log(
            db,
            actor_type="user",
            actor_id=current_user.id,
            action="account.created",
            entity_type="account",
            entity_id=account.id,
            account_id=account.id,
            payload_json=payload.model_dump(mode="json"),
            request=request,
        )
        db.commit()
        db.refresh(account)
        return account
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create account",
        )


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    payload: AccountUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    changes = payload.model_dump(exclude_unset=True)

    if "client_id" in changes:
        client = db.query(Client).filter(Client.id == changes["client_id"]).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

    if "mt5_login" in changes and changes["mt5_login"] != account.mt5_login:
        existing_account = (
            db.query(Account)
            .filter(Account.mt5_login == changes["mt5_login"], Account.id != account.id)
            .first()
        )
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MT5 login already exists",
            )

    for key, value in changes.items():
        setattr(account, key, value)

    try:
        write_audit_log(
            db,
            actor_type="user",
            actor_id=current_user.id,
            action="account.updated",
            entity_type="account",
            entity_id=account.id,
            account_id=account.id,
            payload_json=payload.model_dump(exclude_unset=True, mode="json"),
            request=request,
        )
        db.commit()
        db.refresh(account)
        return account
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update account",
        )
