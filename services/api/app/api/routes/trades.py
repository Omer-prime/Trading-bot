from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.trade import Trade
from app.models.trade_event import TradeEvent
from app.models.user import User
from app.schemas.trade_event import TradeEventRead

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("")
def list_trades(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    trades = db.query(Trade).order_by(Trade.id.desc()).all()
    return trades


@router.get("/{trade_id}")
def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.get("/{trade_id}/events", response_model=list[TradeEventRead])
def get_trade_events(
    trade_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    events = (
        db.query(TradeEvent)
        .filter(TradeEvent.trade_id == trade_id)
        .order_by(TradeEvent.id.asc())
        .all()
    )
    return events