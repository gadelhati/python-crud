# app/config.py - Application configuration settings
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 9000
    root_path: str = ""
    reload: bool = False

    # JWT
    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_access_token_expire_minutes: int = Field(default=30, gt=0)
    jwt_refresh_secret_key: SecretStr = Field(min_length=32)
    jwt_refresh_token_expire_minutes: int = Field(default=60 * 24 * 7, gt=0)

    # Password reset
    password_reset_token_expire_minutes: int = Field(default=30, gt=0)
    password_reset_url: str | None = None

    # SMTP
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, gt=0, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None
    smtp_use_ssl: bool = False
    smtp_starttls: bool = True

    # Database
    database_url: str = Field(min_length=1)

    # Rate limiting
    rate_limit_storage_uri: str = "memory://"
    rate_limit_login: str = "10/minute"
    rate_limit_refresh: str = "10/minute"
    rate_limit_bootstrap: str = "3/minute"
    rate_limit_password_reset: str = "3/minute"

    # CORS
    cors_allow_origins: list[str] = Field(default_factory=list)
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["Authorization", "Content-Type"])
    cors_allow_credentials: bool = False

    @model_validator(mode="after")
    def validate_jwt_secrets(self) -> "Settings":
        if self.jwt_secret_key.get_secret_value() == self.jwt_refresh_secret_key.get_secret_value():
            raise ValueError("JWT access and refresh secrets must be different")
        return self

    @model_validator(mode="after")
    def validate_smtp_transport(self) -> "Settings":
        if self.smtp_use_ssl and self.smtp_starttls:
            raise ValueError("SMTP SSL and STARTTLS cannot be enabled simultaneously")

        has_smtp_credentials = bool(self.smtp_username) or bool(
            self.smtp_password and self.smtp_password.get_secret_value()
        )

        if has_smtp_credentials and not (self.smtp_use_ssl or self.smtp_starttls):
            raise ValueError("SMTP authentication requires SSL or STARTTLS")

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="UVICORN_",
        extra="ignore",
    )


settings = Settings()
