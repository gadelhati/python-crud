# app/services/auth.py - Service for handling authentication,
# login flow, lockout, and token issuance
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.services.base import ServiceError
from app.services.password import verify_password
from app.services.token import (
    create_access_token,
    create_refresh_token,
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
        """Validates credentials and manages lockout. Do NOT expose directly in the API."""
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
            # Persiste o incremento/bloqueio antes de lançar a exceção (evita rollback no get_db)
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

    def refresh(self, refresh_token: str) -> TokenResponse:
        user_id = decode_refresh_token(refresh_token)
        user = self.users.find_by_id(user_id)
        if user is None or not user.is_active:
            raise ServiceError("User inactive or not found", code="invalid_token")
        return self._issue_tokens(user.id)

    @staticmethod
    def _issue_tokens(user_id: UUID) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
