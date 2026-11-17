# app/enum - Enum for permission actions
from enum import StrEnum


class EnumPermissionAction(StrEnum):
    """Enum for permission actions"""

    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    EXECUTE_USER = "execute_user"

    CREATE_ROLE = "create_role"
    READ_ROLE = "read_role"
    UPDATE_ROLE = "update_role"
    DELETE_ROLE = "delete_role"
    EXECUTE_ROLE = "execute_role"

    CREATE_PERMISSION = "create_permission"
    READ_PERMISSION = "read_permission"
    UPDATE_PERMISSION = "update_permission"
    DELETE_PERMISSION = "delete_permission"
    EXECUTE_PERMISSION = "execute_permission"
