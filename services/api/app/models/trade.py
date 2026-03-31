from sqlalchemy import ForeignKey, String, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Trade(TimestampMixin, Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("trading_accounts.id"), index=True)
    mt5_ticket: Mapped[int | None] = mapped_column(Integer, nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), default="XAUUSD")
    side: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(50), default="open")
    lot_size: Mapped[float] = mapped_column(Numeric(10, 4))
    entry_price: Mapped[float] = mapped_column(Numeric(12, 4))
    stop_loss: Mapped[float] = mapped_column(Numeric(12, 4))
    take_profit: Mapped[float] = mapped_column(Numeric(12, 4))
    close_price: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    pnl: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
