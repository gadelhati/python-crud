"""Password reset workflow."""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.base import ServiceError
from app.services.email import send_password_reset_email
from app.services.password import hash_password

logger = logging.getLogger(__name__)

GENERIC_RESPONSE = "If the email address is registered, password reset instructions will be sent."


class ServicePasswordReset:
    """Creates, sends, validates and consumes password reset tokens."""

    generic_response = GENERIC_RESPONSE

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_reset_url(token: str) -> str:
        if not settings.password_reset_url:
            raise RuntimeError("Password reset URL is not configured.")

        parts = urlsplit(settings.password_reset_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["token"] = token

        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query),
                parts.fragment,
            )
        )

    def request_reset(self, email: str) -> tuple[str, str] | None:
        """Create a reset token and return email data for deferred delivery.

        Returning ``None`` for an unknown/ineligible address keeps the public
        response generic. SMTP delivery is deliberately not performed here.
        """

        user = self.db.scalar(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None),
                User.is_active.is_(True),
            )
        )

        if user is None:
            return None

        now = datetime.now(UTC)

        # Only the latest unconsumed token remains valid.
        self.db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
        )

        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=self._hash_token(raw_token),
            expires_at=now + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )

        self.db.add(reset_token)
        self.db.flush()

        try:
            reset_url = self._build_reset_url(raw_token)
        except Exception:
            # Do not disclose account existence or expose the raw token.
            logger.exception("Password reset URL generation failed.")
            self.db.delete(reset_token)
            self.db.flush()
            return None

        return user.email, reset_url

    @staticmethod
    def send_reset_email(recipient: str, reset_url: str) -> None:
        """Deliver the reset email after the HTTP response has been prepared."""

        try:
            send_password_reset_email(recipient, reset_url)
        except Exception:
            # The HTTP response has already been selected; never expose SMTP
            # failures or account existence through the password-reset route.
            logger.exception("Password reset email delivery failed.")

    def confirm_reset(self, token: str, new_password: str) -> None:
        """Consume a valid token and replace the user's password."""

        now = datetime.now(UTC)
        token_hash = self._hash_token(token)

        reset_token = self.db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
            .with_for_update()
        )

        if reset_token is None:
            raise ServiceError("Invalid or expired password reset token.", code="invalid_token")

        user = self.db.scalar(
            select(User).where(
                User.id == reset_token.user_id,
                User.deleted_at.is_(None),
                User.is_active.is_(True),
            )
        )

        if user is None:
            raise ServiceError("Invalid or expired password reset token.", code="invalid_token")

        user.password = hash_password(new_password)
        user.auth_version += 1
        reset_token.used_at = now

        # Invalidate any other outstanding reset token for this account.
        self.db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.id != reset_token.id,
            )
        )

        self.db.flush()
