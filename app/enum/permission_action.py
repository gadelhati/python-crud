# app/enum - Enum for permission actions
from enum import StrEnum


class EnumPermissionAction(StrEnum):
    """Enum for permission actions"""

    CREATE_USER = "create"
    READ_USER = "read"
    UPDATE_USER = "update"
    DELETE_USER = "delete"
    EXECUTE_USER = "execute"

    CREATE_ROLE = "create"
    READ_ROLE = "read"
    UPDATE_ROLE = "update"
    DELETE_ROLE = "delete"
    EXECUTE_ROLE = "execute"

    CREATE_PERMISSION = "create"
    READ_PERMISSION = "read"
    UPDATE_PERMISSION = "update"
    DELETE_PERMISSION = "delete"
    EXECUTE_PERMISSION = "execute"
