from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DraftReply(Base):
    """An AI-drafted email reply, awaiting user review.

    A draft is internal preparation (risk level 1): generating it needs no
    approval. Pushing it to Gmail or sending it crosses into level 3 and goes
    through ActionProposal. The draft holds the proposed content; the
    ActionProposal holds the decision to act on it.
    """

    __tablename__ = "draft_replies"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )

    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    tone: Mapped[str] = mapped_column(String(32), default="concise")  # concise|warm|formal|direct

    # Gmail draft id, set only after the user approves pushing it to Gmail.
    gmail_draft_id: Mapped[str | None] = mapped_column(String(128))
