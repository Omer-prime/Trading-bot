from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class SignalLog(TimestampMixin, Base):
    __tablename__ = "signal_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("trading_accounts.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(50), default="XAUUSD")
    timeframe: Mapped[str] = mapped_column(String(10))
    signal_type: Mapped[str] = mapped_column(String(50))
    direction: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(50), default="detected")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
