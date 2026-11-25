# app/services/auth.py - Service for handling authentication,
# login flow, lockout, and token issuance
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.services.base import ServiceError
from app.services.password import verify_password
from app.services.token import (
    create_access_token,
    create_refresh_token,
    decode_access_token_claims,
    decode_refresh_token,
)

logger = logging.getLogger(__name__)


class ServiceAuth:
    """Login flow: credentials, lockout and token issuance."""

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=60)

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, username: str, password: str) -> User:
        """Validates credentials and manages lockout.
        Do NOT expose directly in the API."""
        invalid = ServiceError("Incorrect username or password", code="invalid_credentials")
        user = self.users.find_by_username_or_email(username)
        if user is None or not user.is_active:
            logger.warning("Failed login for %s", username)
            raise invalid

        now = datetime.now(UTC)
        if user.locked_until is not None:
            locked_until = (
                user.locked_until
                if user.locked_until.tzinfo is not None
                else user.locked_until.replace(tzinfo=UTC)
            )
            if locked_until > now:
                logger.warning("Login attempt on locked account: %s", username)
                raise ServiceError("Account temporarily locked", code="account_locked")
            user.locked_until = None
            user.failed_login_attempts = 0

        if not verify_password(password, user.password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                user.locked_until = now + self.LOCKOUT_DURATION
                logger.warning("Account locked for excessive attempts: %s", username)
            self.db.commit()
            raise invalid

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now
        self.users.save(user)
        return user

    def login(self, username: str, password: str) -> TokenResponse:
        user = self.authenticate(username, password)
        return self._issue_tokens(user.id)

    def _is_token_revoked(self, jti: str) -> bool:
        stmt = select(RevokedToken.jti).where(RevokedToken.jti == jti)
        return self.db.scalar(stmt) is not None

    def _revoke_token(self, jti: str, user_id: UUID, expires_at: datetime) -> None:
        self.db.add(RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at))
        self.db.flush()

    def refresh(self, refresh_token: str) -> TokenResponse:
        """Rotate refresh token: invalidate old, issue new pair.

        Security notes:
        - Old refresh token is immediately revoked (prevents reuse)
        - Treats token reuse as business logic error (401), not server error
        - Handles race condition: if token revoked simultaneously, returns 401
        """
        user_id, jti, expires_at = decode_refresh_token(refresh_token)

        if self._is_token_revoked(jti):
            raise ServiceError(
                "Refresh token has already been used or revoked", code="invalid_token"
            )

        user = self.users.find_by_id(user_id)
        if user is None or not user.is_active:
            raise ServiceError("User inactive or not found", code="invalid_token")

        try:
            self.db.add(RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at))
            self.db.flush()
        except IntegrityError as e:
            raise ServiceError(
                "Refresh token has already been used or revoked", code="invalid_token"
            ) from e

        return self._issue_tokens(user.id)

    def logout(self, access_token: str, refresh_token: str) -> None:
        """Revoke access and refresh tokens during logout."""

        refresh_user_id, refresh_jti, refresh_expires_at = decode_refresh_token(refresh_token)

        try:
            access_user_id, access_jti, access_expires_at = decode_access_token_claims(access_token)
        except ServiceError as exc:
            # An expired access token is already unusable.
            if exc.code != "token_expired":
                raise
        else:
            if access_user_id != refresh_user_id:
                raise ServiceError("Tokens do not belong to the same user", code="invalid_token")

            if not self._is_token_revoked(access_jti):
                self._revoke_token(access_jti, access_user_id, access_expires_at)

        if not self._is_token_revoked(refresh_jti):
            self._revoke_token(refresh_jti, refresh_user_id, refresh_expires_at)

    def purge_expired_tokens(self) -> int:
        """Remove tokens expirados da blacklist para manter a tabela enxuta."""
        stmt = delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(UTC))
        result = self.db.execute(stmt)
        return result.rowcount or 0

    @staticmethod
    def _issue_tokens(user_id: UUID) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
