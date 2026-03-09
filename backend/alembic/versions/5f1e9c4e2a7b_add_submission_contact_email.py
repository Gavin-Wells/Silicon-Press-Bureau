"""add submission contact email

Revision ID: 5f1e9c4e2a7b
Revises: ad7ac8c2bd2d
Create Date: 2026-03-07 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f1e9c4e2a7b"
down_revision: Union[str, None] = "ad7ac8c2bd2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("contact_email", sa.String(length=320), nullable=True))


def downgrade() -> None:
    op.drop_column("submissions", "contact_email")
