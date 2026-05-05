"""add dry run signal observability

Revision ID: a7d8e9f10234
Revises: 9b1c2d3e4f50
Create Date: 2026-05-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7d8e9f10234"
down_revision: Union[str, Sequence[str], None] = "9b1c2d3e4f50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("signal_logs", sa.Column("worker_id", sa.Integer(), nullable=True))
    op.add_column("signal_logs", sa.Column("timeframes_json", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_signal_logs_worker_id"), "signal_logs", ["worker_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_signal_logs_worker_id"), table_name="signal_logs")
    op.drop_column("signal_logs", "timeframes_json")
    op.drop_column("signal_logs", "worker_id")
