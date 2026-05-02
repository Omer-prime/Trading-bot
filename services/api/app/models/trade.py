from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Trade(TimestampMixin, Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("trading_accounts.id"), index=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("signal_logs.id"), nullable=True)

    external_ticket: Mapped[str | None] = mapped_column(String(100), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50))
    direction: Mapped[str] = mapped_column(String(20))

    lot_size: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)

    closed_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    rr_realized: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="open")
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="trades")
    signal: Mapped["SignalLog | None"] = relationship("SignalLog", back_populates="trades")

    trade_events: Mapped[list["TradeEvent"]] = relationship(
        "TradeEvent",
        back_populates="trade",
        cascade="all, delete-orphan",
    )