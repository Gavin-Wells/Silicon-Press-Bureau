"""add newspaper configs table

Revision ID: c6a1d9b4e8f2
Revises: 5f1e9c4e2a7b
Create Date: 2026-03-08 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6a1d9b4e8f2"
down_revision: Union[str, None] = "5f1e9c4e2a7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "newspaper_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("newspaper_id", sa.Integer(), nullable=False),
        sa.Column("review_prompt", sa.Text(), nullable=True),
        sa.Column("edit_prompt", sa.Text(), nullable=True),
        sa.Column("reject_prompt", sa.Text(), nullable=True),
        sa.Column("scoring_profile", sa.JSON(), nullable=True),
        sa.Column("issue_config", sa.JSON(), nullable=True),
        sa.Column("news_config", sa.JSON(), nullable=True),
        sa.Column("invite_config", sa.JSON(), nullable=True),
        sa.Column("publish_config", sa.JSON(), nullable=True),
        sa.Column("rejection_letter_style", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["newspaper_id"], ["newspapers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("newspaper_id"),
    )
    op.create_index(op.f("ix_newspaper_configs_id"), "newspaper_configs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_newspaper_configs_id"), table_name="newspaper_configs")
    op.drop_table("newspaper_configs")
