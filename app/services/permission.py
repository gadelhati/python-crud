from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.enum.permission_action import EnumPermissionAction
from app.models.permission import Permission
from app.repositories.permission import PermissionRepository
from app.schemas.permission import DTOPermissionRetrieve
from app.services.base import ServiceBase


class ServicePermission(ServiceBase[Permission, BaseModel, BaseModel, DTOPermissionRetrieve]):
    """Permission service (read-only: expose only get/list in the routes)."""

    def __init__(self, db: Session) -> None:
        self.permissions = PermissionRepository(db)
        super().__init__(db, self.permissions, DTOPermissionRetrieve)

    def get_by_action(
        self, action: EnumPermissionAction, include_deleted: bool = False
    ) -> list[DTOPermissionRetrieve]:
        found = self.permissions.find_by_action(action, include_deleted=include_deleted)
        return [self._to_dto(p) for p in found]

    def sync_with_enum(self) -> None:
        """Ensures every enum value exists in the DB (idempotent)."""
        existing = self.permissions.find_all_actions()
        for action in EnumPermissionAction:
            if action.value not in existing:
                self.permissions.save(Permission(action=action.value))
        self._commit()
