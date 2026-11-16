from pydantic import EmailStr, Field, field_validator

from app.schemas.base import SchemaBase
from app.validations.user import UserValidation


class LoginRequest(SchemaBase):
    """Schema for authentication requests."""

    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()

        if len(v) < UserValidation.USERNAME_MIN_LENGTH:
            raise ValueError(
                f"Username or email must be at least "
                f"{UserValidation.USERNAME_MIN_LENGTH} characters"
            )

        return v


class TokenResponse(SchemaBase):
    """Schema for authentication token responses."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(ge=0)


class PasswordResetRequest(SchemaBase):
    """Schema for password reset requests."""

    email: EmailStr


class PasswordResetConfirmRequest(SchemaBase):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(
        min_length=UserValidation.PASSWORD_MIN_LENGTH, max_length=UserValidation.PASSWORD_MAX_LENGTH
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return UserValidation.validate_password(v)
