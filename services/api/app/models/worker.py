from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Worker(TimestampMixin, Base):
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("trading_accounts.id"), index=True)

    machine_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="offline", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dry_run_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="workers")

    __table_args__ = (
        Index(
            "ix_workers_one_active_per_account",
            "account_id",
            unique=True,
            postgresql_where=is_active.is_(True),
            sqlite_where=is_active.is_(True),
        ),
    )
