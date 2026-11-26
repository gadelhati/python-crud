"""SMTP email delivery."""

import smtplib
from email.message import EmailMessage

from app.config import settings


def send_password_reset_email(recipient: str, reset_url: str) -> None:
    """Send a password reset link using the configured SMTP server."""

    if not settings.smtp_host or not settings.smtp_from:
        raise RuntimeError("SMTP host and sender must be configured.")

    message = EmailMessage()
    message["Subject"] = "Password reset"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(
        "A password reset was requested for your account.\n\n"
        f"Use the following link to choose a new password:\n{reset_url}\n\n"
        "If you did not request this change, ignore this message."
    )

    password = (
        settings.smtp_password.get_secret_value() if settings.smtp_password is not None else None
    )

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=15,
        ) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, password or "")
            server.send_message(message)
        return

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=15,
    ) as server:
        server.ehlo()

        if settings.smtp_starttls:
            server.starttls()
            server.ehlo()

        if settings.smtp_username:
            server.login(settings.smtp_username, password or "")

        server.send_message(message)
