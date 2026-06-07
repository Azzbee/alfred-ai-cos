"""add people + projects + back-references on messages and commitments

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-07 11:30:00.000000

PRD 15.1 memory entities. Person is keyed by (user_id, email_lower) and
back-referenced from Message.sender_person_id and
Commitment.counterparty_person_id. Project is back-referenced from
Commitment.project_id. Both tables CASCADE on user delete; the FK columns
on messages/commitments use SET NULL so deleting a person doesn't lose
the message itself."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "people",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email_lower", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("organization", sa.String(length=200), nullable=True),
        sa.Column(
            "relationship_type",
            sa.String(length=32),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "relationship_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "importance_weight",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column("inbound_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outbound_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "last_interaction_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", "email_lower", name="uq_person_user_email"),
    )
    op.create_index("ix_people_user_id", "people", ["user_id"])
    op.create_index("ix_people_email_lower", "people", ["email_lower"])
    op.create_index("ix_people_organization", "people", ["organization"])
    op.create_index("ix_people_last_interaction_at", "people", ["last_interaction_at"])

    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("related_people", sa.JSON(), nullable=True),
        sa.Column("keyword_tokens", sa.JSON(), nullable=True),
        sa.Column(
            "is_proposed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])

    op.add_column(
        "messages",
        sa.Column(
            "sender_person_id",
            sa.String(),
            sa.ForeignKey("people.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_messages_sender_person_id", "messages", ["sender_person_id"])

    op.add_column(
        "commitments",
        sa.Column(
            "counterparty_person_id",
            sa.String(),
            sa.ForeignKey("people.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "commitments",
        sa.Column(
            "project_id",
            sa.String(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_commitments_counterparty_person_id",
        "commitments",
        ["counterparty_person_id"],
    )
    op.create_index("ix_commitments_project_id", "commitments", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_commitments_project_id", table_name="commitments")
    op.drop_index("ix_commitments_counterparty_person_id", table_name="commitments")
    op.drop_column("commitments", "project_id")
    op.drop_column("commitments", "counterparty_person_id")
    op.drop_index("ix_messages_sender_person_id", table_name="messages")
    op.drop_column("messages", "sender_person_id")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_people_last_interaction_at", table_name="people")
    op.drop_index("ix_people_organization", table_name="people")
    op.drop_index("ix_people_email_lower", table_name="people")
    op.drop_index("ix_people_user_id", table_name="people")
    op.drop_table("people")
