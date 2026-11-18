# app/validations/role.py - Centralized validation rules for
# role-related data
from pydantic import field_validator


class RoleValidation:
    """Centralized role validation rules."""

    NAME_MIN_LENGTH = 3
    NAME_MAX_LENGTH = 100

    DESCRIPTION_MIN_LENGTH = 0
    DESCRIPTION_MAX_LENGTH = 100

    MAX_PERMISSIONS_PER_ROLE = 50

    @staticmethod
    def validate_name(v: str | None, field_name: str = "Role name") -> str | None:
        """Normalize a role field and reject non-null blank values."""
        if v is None:
            return None
        result = v.strip()
        if not result:
            raise ValueError(f"{field_name} is required")
        return result

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        return RoleValidation.validate_name(v, "Description")
