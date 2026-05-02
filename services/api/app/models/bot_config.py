from sqlalchemy import ForeignKey, String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class BotConfig(TimestampMixin, Base):
    __tablename__ = "bot_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("trading_accounts.id"), unique=True)
    entry_timeframe: Mapped[str] = mapped_column(String(10), default="M5")
    confirmation_timeframe: Mapped[str] = mapped_column(String(10), default="H1")
    bias_timeframe: Mapped[str] = mapped_column(String(10), default="H4")
    risk_per_trade_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=1.00)
    min_rr: Mapped[float] = mapped_column(Numeric(5, 2), default=2.00)
    break_even_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    trailing_stop_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    trend_only: Mapped[bool] = mapped_column(Boolean, default=True)
    london_newyork_only: Mapped[bool] = mapped_column(Boolean, default=True)
    news_filter_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    account = relationship("Account", back_populates="bot_config")
