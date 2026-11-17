# app/models/permission.py - Permission model representing
# actions that can be assigned to roles
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enum.permission_action import EnumPermissionAction
from app.models.base import EntityBase
from app.models.join import role_permissions

if TYPE_CHECKING:
    from app.models.role import Role


class Permission(EntityBase):
    """Permission model"""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    action: Mapped[EnumPermissionAction] = mapped_column(
        Enum(
            EnumPermissionAction,
            name="enum_permission_action",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        doc="Action type for this permission",
    )

    """Relationships"""
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        order_by="Role.name",
        doc="Roles that have this permission",
    )

    def __repr__(self) -> str:
        return (
            f"Permission("
            f"name='{self.name}', "
            f"action='{self.action.value if hasattr(self.action, 'value') else self.action}'"
            f")"
        )
