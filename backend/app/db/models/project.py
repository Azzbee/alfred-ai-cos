"""The Project entity (PRD 15.1).

Albert's project memory. A project groups related commitments, messages,
and people. Examples from PRD: "Barnes Dubai Acquisition", "Q4 fundraise",
"product launch". Two creation paths:

  - **User-created**: the user names a project on the Projects screen and
    starts attaching commitments to it explicitly.
  - **LLM-clustered**: the project service runs over the user's open
    commitments and proposes clusters based on shared counterparties +
    keyword overlap + thread continuity. Proposed projects are stored with
    `is_proposed=True` until the user accepts or rejects them.

Back-references live on Commitment (`project_id`) and through Person via
the Project's `related_people` JSON column (sender-emails, lowercased)."""

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(String(16), default=ProjectStatus.active)

    # Email addresses associated with this project (sender + counterparty).
    # Stored as a flat lowercased list for cheap membership tests.
    related_people: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Optional explicit cluster of keyword tokens — set when the LLM extracts
    # a project from a commitment cluster. The Projects screen uses these as
    # a "what's in this project" hint.
    keyword_tokens: Mapped[list[str]] = mapped_column(JSON, default=list)

    # True when the project was auto-clustered and the user hasn't accepted
    # it yet. Proposed projects show on the Projects screen as suggestions;
    # accepted projects move to the main list.
    is_proposed: Mapped[bool] = mapped_column(Boolean, default=False)
