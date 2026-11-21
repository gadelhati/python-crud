# app/repositories/role.py - Repository for managing Role
# entities with support for soft deletion
from collections.abc import Sequence

from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.repositories.base import SoftDeleteRepository


class RoleRepository(SoftDeleteRepository[Role]):
    model = Role

    def find_by_name(self, name: str, *, include_deleted: bool = False) -> Role | None:
        stmt = self._select(include_deleted=include_deleted).where(Role.name == name)
        return self.db.scalar(stmt)

    def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> Sequence[Role]:
        stmt = (
            self._select(include_deleted=include_deleted)
            .options(selectinload(Role.permissions))
            .order_by(Role.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def find_defaults(self, *, include_deleted: bool = False) -> list[Role]:
        stmt = self._select(include_deleted=include_deleted).where(Role.is_default.is_(True))
        return list(self.db.scalars(stmt))
