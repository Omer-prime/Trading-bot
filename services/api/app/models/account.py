from sqlalchemy import String, ForeignKey, Boolean, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class TradingAccount(TimestampMixin, Base):
    __tablename__ = "trading_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    broker_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mt5_login: Mapped[str] = mapped_column(String(100), unique=True)
    server_name: Mapped[str] = mapped_column(String(255))
    account_mode: Mapped[str] = mapped_column(String(50), default="monitor")
    symbol: Mapped[str] = mapped_column(String(50), default="XAUUSD")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_daily_loss_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=3.00)
    max_open_trades: Mapped[int] = mapped_column(Integer, default=1)

    client = relationship("Client", back_populates="accounts")
    bot_config = relationship("BotConfig", back_populates="account", uselist=False)
