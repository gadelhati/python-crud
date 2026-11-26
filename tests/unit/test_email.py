"""Tests for SMTP email delivery."""

from email.message import EmailMessage

import pytest
from pydantic import SecretStr

from app.config import settings
from app.services.email import send_password_reset_email


class FakeSMTP:
    """SMTP test double."""

    instances: list["FakeSMTP"] = []

    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.calls: list[tuple] = []
        self.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def ehlo(self) -> None:
        self.calls.append(("ehlo",))

    def starttls(self) -> None:
        self.calls.append(("starttls",))

    def login(self, username: str, password: str) -> None:
        self.calls.append(("login", username, password))

    def send_message(self, message: EmailMessage) -> None:
        self.calls.append(("send_message", message))


@pytest.fixture(autouse=True)
def reset_smtp_instances() -> None:
    FakeSMTP.instances.clear()


def test_send_email_requires_smtp_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_from", None)

    with pytest.raises(RuntimeError, match="SMTP host and sender"):
        send_password_reset_email("user@example.com", "https://example.com/reset")


def test_send_email_uses_ssl_and_authentication(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_port", 465)
    monkeypatch.setattr(settings, "smtp_use_ssl", True)
    monkeypatch.setattr(settings, "smtp_starttls", False)
    monkeypatch.setattr(settings, "smtp_username", "smtp-user")
    monkeypatch.setattr(settings, "smtp_password", SecretStr("smtp-password"))

    monkeypatch.setattr("app.services.email.smtplib.SMTP_SSL", FakeSMTP)

    send_password_reset_email(
        "user@example.com",
        "https://example.com/reset?token=abc",
    )

    server = FakeSMTP.instances[0]

    assert server.host == "smtp.example.com"
    assert server.port == 465
    assert ("login", "smtp-user", "smtp-password") in server.calls

    message = next(call[1] for call in server.calls if call[0] == "send_message")
    assert message["To"] == "user@example.com"
    assert message["From"] == "noreply@example.com"
    assert "abc" in message.get_content()


def test_send_email_uses_starttls_and_authentication(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_use_ssl", False)
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_username", "smtp-user")
    monkeypatch.setattr(settings, "smtp_password", SecretStr("smtp-password"))

    monkeypatch.setattr("app.services.email.smtplib.SMTP", FakeSMTP)

    send_password_reset_email(
        "user@example.com",
        "https://example.com/reset?token=abc",
    )

    server = FakeSMTP.instances[0]

    assert ("ehlo",) in server.calls
    assert ("starttls",) in server.calls
    assert server.calls.count(("ehlo",)) == 2
    assert ("login", "smtp-user", "smtp-password") in server.calls
    assert any(call[0] == "send_message" for call in server.calls)


def test_send_email_without_authentication_or_starttls(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_port", 25)
    monkeypatch.setattr(settings, "smtp_use_ssl", False)
    monkeypatch.setattr(settings, "smtp_starttls", False)
    monkeypatch.setattr(settings, "smtp_username", None)
    monkeypatch.setattr(settings, "smtp_password", None)

    monkeypatch.setattr("app.services.email.smtplib.SMTP", FakeSMTP)

    send_password_reset_email(
        "user@example.com",
        "https://example.com/reset",
    )

    server = FakeSMTP.instances[0]

    assert ("ehlo",) in server.calls
    assert not any(call[0] == "starttls" for call in server.calls)
    assert not any(call[0] == "login" for call in server.calls)
    assert any(call[0] == "send_message" for call in server.calls)
