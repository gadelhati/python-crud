# app/repository/base.py
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User
from app.repositories.base import SoftDeleteRepository


class UserRepository(SoftDeleteRepository[User]):
    model = User

    def find_by_username(self, username: str, *, include_deleted: bool = False) -> User | None:
        stmt = self._select(include_deleted=include_deleted).where(User.username == username)
        return self.db.scalar(stmt)

    def find_by_email(self, email: str, *, include_deleted: bool = False) -> User | None:
        stmt = self._select(include_deleted=include_deleted).where(User.email == email)
        return self.db.scalar(stmt)

    def find_by_username_or_email(
        self, identifier: str, *, include_deleted: bool = False
    ) -> User | None:
        stmt = (
            self._select(include_deleted=include_deleted)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(or_(User.username == identifier, User.email == identifier))
        )
        return self.db.scalar(stmt)
