# app/repositories/user.py
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entities."""

    model = User

    def find_all(self, *, offset: int = 0, limit: int = 100) -> list[User]:
        """Returns active users with pagination."""
        stmt = (
            select(self.model)
            .where(self.model.deleted_at.is_(None))
            .order_by(self.model.id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def find_by_id(self, id: UUID) -> User | None:
        """Returns an active user by ID, or None if absent or soft-deleted."""
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def find_by_username(self, username: str) -> User | None:
        """Returns an active user by username, or None if absent."""
        stmt = select(self.model).where(
            self.model.username == username,
            self.model.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def soft_delete_by_id(self, id: UUID) -> bool:
        """Marks an active user as deleted. Returns True if it existed."""
        user = self.find_by_id(id)
        if user is None:
            return False
        user.deleted_at = datetime.now(UTC)
        self.db.flush()
        return True

    def restore_by_id(self, id: UUID) -> User | None:
        """Restores a soft-deleted user, or returns None when not restorable."""
        user = self.db.get(self.model, id)
        if user is None or user.deleted_at is None:
            return None
        user.deleted_at = None
        self.db.flush()
        self.db.refresh(user)
        return user
