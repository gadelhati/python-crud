# app/config.py - Application configuration settings,
# including server, JWT, and database settings
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
    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_access_token_expire_minutes: int = Field(default=30, gt=0)
    jwt_refresh_secret_key: SecretStr = Field(min_length=32)
    jwt_refresh_token_expire_minutes: int = Field(default=60 * 24 * 7, gt=0)
    database_url: str = Field(min_length=1)
    rate_limit_storage_uri: str = "memory://"
    rate_limit_login: str = "10/minute"
    rate_limit_refresh: str = "10/minute"
    rate_limit_bootstrap: str = "3/minute"

    @model_validator(mode="after")
    def validate_jwt_secrets(self) -> "Settings":
        if self.jwt_secret_key.get_secret_value() == self.jwt_refresh_secret_key.get_secret_value():
            raise ValueError("JWT access and refresh secrets must be different")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="UVICORN_",
        extra="ignore",
    )


settings = Settings()
