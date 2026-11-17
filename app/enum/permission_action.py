# app/enum - Enum for permission actions
from enum import StrEnum


class EnumPermissionAction(StrEnum):
    """Enum for permission actions"""

    CREATE_USER = "create:user"
    READ_USER = "read:user"
    UPDATE_USER = "update:user"
    DELETE_USER = "delete:user"
    EXECUTE_USER = "execute:user"

    CREATE_ROLE = "create:role"
    READ_ROLE = "read:role"
    UPDATE_ROLE = "update:role"
    DELETE_ROLE = "delete:role"
    EXECUTE_ROLE = "execute:role"

    CREATE_PERMISSION = "create:permission"
    READ_PERMISSION = "read:permission"
    UPDATE_PERMISSION = "update:permission"
    DELETE_PERMISSION = "delete:permission"
    EXECUTE_PERMISSION = "execute:permission"
