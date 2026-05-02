from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.id.desc()).all()


@router.post("", response_model=AccountRead)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
