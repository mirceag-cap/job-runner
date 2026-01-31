"""add failed_at, last_error and last_error_at fields

Revision ID: bfa0dc02879b
Revises: f47ff4fa4f25
Create Date: 2026-01-25 15:07:25.610306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfa0dc02879b'
down_revision: Union[str, Sequence[str], None] = 'f47ff4fa4f25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("last_error", sa.Text(), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "last_error_at")
    op.drop_column("jobs", "last_error")
    op.drop_column("jobs", "failed_at")