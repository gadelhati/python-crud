# directory containing the representation of the entities
from app.models.base import Base, EntityBase
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

__all__ = [
    "Base",
    "EntityBase",
    "Permission",
    "Role",
    "User",
]
