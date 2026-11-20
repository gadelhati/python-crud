# app/validations/user.py - Centralized validation rules for
#  user-related data
import re


class UserValidation:
    """Centralized user validation rules."""

    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 100

    EMAIL_MIN_LENGTH = 3
    EMAIL_MAX_LENGTH = 100

    PASSWORD_MIN_LENGTH = 12
    PASSWORD_MAX_LENGTH = 128

    NAME_MIN_LENGTH = 1
    NAME_MAX_LENGTH = 100

    MIN_ROLES_PER_USER = 1
    MAX_ROLES_PER_USER = 10

    @staticmethod
    def validate_username(v: str) -> str:
        v = v.strip()
        if not UserValidation.USERNAME_MIN_LENGTH <= len(v) <= UserValidation.USERNAME_MAX_LENGTH:
            raise ValueError(
                f"Username must contain between "
                f"{UserValidation.USERNAME_MIN_LENGTH} and "
                f"{UserValidation.USERNAME_MAX_LENGTH} characters"
            )
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", v):
            raise ValueError(
                "Username must contain only letters, numbers, underscores, dots and hyphens"
            )
        return v

    @staticmethod
    def validate_password(v: str) -> str:
        if not UserValidation.PASSWORD_MIN_LENGTH <= len(v) <= UserValidation.PASSWORD_MAX_LENGTH:
            raise ValueError(
                f"Password must contain between "
                f"{UserValidation.PASSWORD_MIN_LENGTH} and "
                f"{UserValidation.PASSWORD_MAX_LENGTH} characters"
            )
        return v

    @staticmethod
    def validate_names(v: str | None, field_name: str) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError(f"{field_name} cannot be empty")
        if len(v) < UserValidation.NAME_MIN_LENGTH:
            raise ValueError(
                f"{field_name} must contain at least {UserValidation.NAME_MIN_LENGTH} characters"
            )
        if len(v) > UserValidation.NAME_MAX_LENGTH:
            raise ValueError(
                f"{field_name} must contain at most {UserValidation.NAME_MAX_LENGTH} characters"
            )
        return v

    @staticmethod
    def validate_collection_size(
        values: list,
        max_length: int,
        field_name: str,
    ) -> list:
        if len(values) < UserValidation.MIN_ROLES_PER_USER:
            raise ValueError(f"{field_name} must contain at least {UserValidation.MIN_ROLES_PER_USER} items")
        if len(values) > UserValidation.MAX_ROLES_PER_USER:
            raise ValueError(f"{field_name} must contain at most {UserValidation.MAX_ROLES_PER_USER} items")

        return values
