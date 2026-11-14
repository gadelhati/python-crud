from sqlalchemy import select

from app.enum.permission_action import EnumPermissionAction
from app.models.permission import Permission
from app.repositories.base import SoftDeleteRepository


class PermissionRepository(SoftDeleteRepository[Permission]):
    model = Permission

    def find_by_action(
        self, action: EnumPermissionAction, *, include_deleted: bool = False
    ) -> list[Permission]:
        stmt = self._select(include_deleted=include_deleted).where(
            Permission.action == action.value
        )
        return list(self.db.scalars(stmt))

    def find_all_actions(self) -> set[str]:
        """Actions already stored, including soft-deleted ones."""
        return set(self.db.scalars(select(Permission.action)))
