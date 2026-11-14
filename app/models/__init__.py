# directory containing the representation of the entities
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

__all__ = ["User", "user_roles", "Role", "role_permissions", "Permission"]
