from __future__ import annotations

from decimal import Decimal

from sqlalchemy import String, ForeignKey, Numeric, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class SignalLog(TimestampMixin, Base):
    __tablename__ = "signal_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("trading_accounts.id"), index=True)

    symbol: Mapped[str] = mapped_column(String(50), default="XAUUSD")
    timeframe: Mapped[str] = mapped_column(String(20))
    direction: Mapped[str] = mapped_column(String(20))

    trend_bias: Mapped[str | None] = mapped_column(String(20), nullable=True)
    liquidity_sweep_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    bos_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    rr_estimate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="new")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="signals")
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="signal")
