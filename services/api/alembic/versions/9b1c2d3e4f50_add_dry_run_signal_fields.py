"""add dry run signal fields

Revision ID: 9b1c2d3e4f50
Revises: 7c2a4d8e9f10
Create Date: 2026-05-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b1c2d3e4f50"
down_revision: Union[str, Sequence[str], None] = "7c2a4d8e9f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("workers", sa.Column("dry_run_summary", sa.JSON(), nullable=True))
    op.add_column("signal_logs", sa.Column("rr_estimate", sa.Numeric(10, 4), nullable=True))
    op.add_column("signal_logs", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("signal_logs", sa.Column("payload_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("signal_logs", "payload_json")
    op.drop_column("signal_logs", "rejection_reason")
    op.drop_column("signal_logs", "rr_estimate")
    op.drop_column("workers", "dry_run_summary")
