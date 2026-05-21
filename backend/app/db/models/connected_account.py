from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import Provider, SyncStatus


class ConnectedAccount(Base):
    """An external integration (Google for Gmail + Calendar in the slice).

    OAuth tokens are stored encrypted via app.services.crypto. The encrypted
    blob lives in `token_ciphertext`; raw tokens never touch the database.
    """

    __tablename__ = "connected_accounts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[Provider] = mapped_column(String(32))
    provider_account_email: Mapped[str | None] = mapped_column(String(320))

    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    token_ciphertext: Mapped[str] = mapped_column(Text)

    sync_status: Mapped[SyncStatus] = mapped_column(String(16), default=SyncStatus.never)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_error: Mapped[str | None] = mapped_column(Text)
