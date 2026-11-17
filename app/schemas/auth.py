from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.schemas.base import SchemaBase
from app.validations.user import UserValidation


class LoginRequest(SchemaBase):
    """Schema for authentication requests."""

    model_config = ConfigDict(str_strip_whitespace=False)

    username: str = Field(
        min_length=UserValidation.USERNAME_MIN_LENGTH, max_length=UserValidation.USERNAME_MAX_LENGTH
    )
    password: str = Field(
        min_length=UserValidation.PASSWORD_MIN_LENGTH, max_length=UserValidation.PASSWORD_MAX_LENGTH
    )

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
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = Field(ge=0)


class RefreshTokenRequest(SchemaBase):
    """Schema for refreshing an expired access token."""

    refresh_token: str = Field(min_length=1)


class PasswordResetRequest(SchemaBase):
    """Schema for password reset requests."""

    email: EmailStr = Field(max_length=UserValidation.PASSWORD_MAX_LENGTH)


class PasswordResetConfirmRequest(SchemaBase):
    """Schema for password reset confirmation."""

    model_config = ConfigDict(str_strip_whitespace=False)

    token: str = Field(min_length=1)
    new_password: str = Field(
        min_length=UserValidation.PASSWORD_MIN_LENGTH, max_length=UserValidation.PASSWORD_MAX_LENGTH
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return UserValidation.validate_password(v)
