# app/validations/role.py - Centralized validation rules for
# role-related data


class RoleValidation:
    """Centralized role validation rules."""

    NAME_MIN_LENGTH = 3
    NAME_MAX_LENGTH = 100

    DESCRIPTION_MIN_LENGTH = 0
    DESCRIPTION_MAX_LENGTH = 100

    MAX_PERMISSIONS_PER_ROLE = 50
