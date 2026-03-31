from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import TradingAccount
from app.schemas.account import TradingAccountCreate, TradingAccountRead

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[TradingAccountRead])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(TradingAccount).order_by(TradingAccount.id.desc()).all()


@router.post("", response_model=TradingAccountRead)
def create_account(payload: TradingAccountCreate, db: Session = Depends(get_db)):
    account = TradingAccount(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
