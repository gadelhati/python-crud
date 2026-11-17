from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RevokedToken(Base):
    """Stores revoked JWT IDs (jti) until their expiration."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(UTC), nullable=False, index=True)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(UTC), default=lambda: datetime.now(UTC), nullable=False
    )
