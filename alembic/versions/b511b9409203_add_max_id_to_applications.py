"""add max_id to applications

Revision ID: b511b9409203
Revises: 0e58fe12b069
Create Date: 2026-09-25 15:18:13.600023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b511b9409203'
down_revision: Union[str, None] = '0e58fe12b069'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "applications", sa.Column("max_id", sa.Integer(), nullable=True)
    )
    op.execute("UPDATE applications SET max_id = 0")
    op.alter_column(
        "applications",
        "max_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("applications", "max_id")
