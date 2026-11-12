# app/repositories/base.py
from collections.abc import Sequence
from typing import TypeVar
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository[T: Base]:
    """Generic repository for entities with a UUID primary key."""

    model: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    def find_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[T]:
        """Returns all records, with pagination."""
        stmt = select(self.model).order_by(self.model.id).offset(offset).limit(limit)
        return self.db.scalars(stmt).all()

    def count(self) -> int:
        """Returns the total count of records."""
        return self.db.scalar(select(func.count()).select_from(self.model)) or 0

    def find_by_id(self, id: UUID) -> T | None:
        """Returns the record by ID, or None if it doesn't exist."""
        return self.db.get(self.model, id)

    def exists_by_id(self, id: UUID) -> bool:
        """Checks if a record with the given ID exists."""
        return bool(self.db.scalar(select(exists().where(self.model.id == id))))

    def save(self, entity: T) -> T:
        """Inserts or updates. Does not commit: the caller controls the transaction."""
        if entity.id is not None:
            entity = self.db.merge(entity)
        else:
            self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def delete_by_id(self, id: UUID) -> bool:
        """Permanently deletes a record by ID. Returns True if it existed."""
        entity = self.db.get(self.model, id)
        if entity is None:
            return False
        self.db.delete(entity)
        self.db.flush()
        return True
