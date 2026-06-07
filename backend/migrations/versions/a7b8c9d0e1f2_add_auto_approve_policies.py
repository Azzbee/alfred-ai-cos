"""add auto_approve_policies

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-07 14:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auto_approve_policies",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("counterparty_email", sa.String(length=320), nullable=True),
        sa.Column("counterparty_domain", sa.String(length=200), nullable=True),
        sa.Column("max_cents", sa.Integer(), nullable=True),
        sa.Column("content_substring", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("active_window", sa.String(length=16), nullable=True),
        sa.Column(
            "fire_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("meta", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_auto_approve_policies_user_id",
        "auto_approve_policies",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auto_approve_policies_user_id",
        table_name="auto_approve_policies",
    )
    op.drop_table("auto_approve_policies")
