"""Tests for application configuration validation."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def build_settings(**overrides) -> Settings:
    values = {
        "jwt_secret_key": "a" * 32,
        "jwt_refresh_secret_key": "b" * 32,
        "database_url": "sqlite://",
    }
    values.update(overrides)
    return Settings(**values)


def test_jwt_secrets_must_be_different() -> None:
    with pytest.raises(ValidationError, match="JWT access and refresh secrets"):
        build_settings(
            jwt_secret_key="a" * 32,
            jwt_refresh_secret_key="a" * 32,
        )


def test_smtp_ssl_and_starttls_cannot_be_enabled_together() -> None:
    with pytest.raises(
        ValidationError,
        match="SMTP SSL and STARTTLS cannot be enabled simultaneously",
    ):
        build_settings(
            smtp_use_ssl=True,
            smtp_starttls=True,
        )


@pytest.mark.parametrize(
    ("smtp_use_ssl", "smtp_starttls"),
    [
        (True, False),
        (False, True),
        (False, False),
    ],
)
def test_valid_smtp_transport_configurations(
    smtp_use_ssl: bool,
    smtp_starttls: bool,
) -> None:
    config = build_settings(
        smtp_use_ssl=smtp_use_ssl,
        smtp_starttls=smtp_starttls,
    )

    assert config.smtp_use_ssl is smtp_use_ssl
    assert config.smtp_starttls is smtp_starttls
