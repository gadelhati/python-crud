import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse
from app.services.base import ServiceError
from app.services.password import verify_password
from app.services.token import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
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
        user = self.users.find_by_username(username)
        if user is None or not user.is_active:
            logger.warning("Failed login for %s", username)
            raise invalid

        now = datetime.now(UTC)
        if user.locked_until is not None:
            if user.locked_until > now:
                logger.warning("Login attempt on locked account: %s", username)
                raise ServiceError("Account temporarily locked", code="account_locked")
            user.locked_until = None  # lock expired
            user.failed_login_attempts = 0

        if not verify_password(password, user._password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                user.locked_until = now + self.LOCKOUT_DURATION
                logger.warning("Account locked for excessive attempts: %s", username)
            self.db.commit()
            raise invalid

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now
        self.db.commit()
        return user

    def login(self, username: str, password: str) -> dict[str, str]:
        user = self.authenticate(username, password)
        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }

    def refresh(self, refresh_token: str) -> dict[str, str]:
        user = self._active_user(decode_refresh_token(refresh_token))
        return {"access_token": create_access_token(user.id), "token_type": "bearer"}

    def get_current_user(self, token: str) -> UserResponse:
        user = self._active_user(decode_access_token(token))
        return UserResponse.model_validate(user, from_attributes=True)

    def _active_user(self, user_id: UUID) -> User:
        user = self.users.find_by_id(user_id)
        if user is None or not user.is_active:
            raise ServiceError("User not found", code="not_found")
        return user
