"""add active worker uniqueness

Revision ID: 7c2a4d8e9f10
Revises: dbadfc1c9d03
Create Date: 2026-05-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c2a4d8e9f10"
down_revision: Union[str, Sequence[str], None] = "dbadfc1c9d03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_workers_one_active_per_account",
        "workers",
        ["account_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
        sqlite_where=sa.text("is_active = 1"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_workers_one_active_per_account", table_name="workers")
