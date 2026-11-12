# app/models/user.py
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import EntityBase, Role, TimestampMixin
from app.models.join import user_roles


class User(TimestampMixin, EntityBase):
    """User entity representing a user in the system."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, doc="Whether user account is active"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, doc="Whether user email is verified"
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(UTC), doc="Last successful login timestamp"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, doc="Count of consecutive failed login attempts"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(UTC), doc="Account lock expiration timestamp"
    )

    """Relationships"""
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        order_by="Role.name",
        doc="Roles assigned to the user",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"
