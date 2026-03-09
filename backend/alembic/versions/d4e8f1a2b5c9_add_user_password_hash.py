"""add user password_hash

Revision ID: d4e8f1a2b5c9
Revises: c6a1d9b4e8f2
Create Date: 2026-03-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e8f1a2b5c9"
down_revision: Union[str, None] = "c6a1d9b4e8f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
