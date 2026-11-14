import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import DTOUserCreate, DTOUserUpdate, UserRetrieve
from app.services.base import ServiceBase
from app.services.password import hash_password
from app.validations.validation import Validation

logger = logging.getLogger(__name__)


class ServiceUser(ServiceBase[User, DTOUserCreate, DTOUserUpdate, UserRetrieve]):
    """User service with user-specific rules."""

    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        super().__init__(db, self.users, UserRetrieve)

    def get_by_email(self, email: str, include_deleted: bool = False) -> UserRetrieve | None:
        user = self.users.find_by_email(email, include_deleted=include_deleted)
        return self._to_dto(user) if user else None

    def get_by_username(self, username: str, include_deleted: bool = False) -> UserRetrieve | None:
        user = self.users.find_by_username(username, include_deleted=include_deleted)
        return self._to_dto(user) if user else None

    def update_roles(
        self, user_id: UUID, role_ids: list[UUID], current_user_id: UUID | None = None
    ) -> UserRetrieve:
        self._validate_ids(role_ids, Validation.MAX_ROLES_PER_USER, "roles")
        user = self._get_or_404(user_id)
        roles = self.roles.find_by_ids(role_ids)
        self._check_found(roles, role_ids, "roles")

        user.roles = list(roles)
        self._stamp(user, current_user_id)
        self._commit()
        return self._to_dto(user)

    def set_password(
        self, user_id: UUID, password: str, current_user_id: UUID | None = None
    ) -> bool:
        user = self._get_or_404(user_id)
        user._password_hash = hash_password(password)
        self._stamp(user, current_user_id)
        self._commit()
        return True

    def unlock_account(self, user_id: UUID, current_user_id: UUID | None = None) -> bool:
        """Manual unlock (admins only)."""
        user = self._get_or_404(user_id)
        user.failed_login_attempts = 0
        user.locked_until = None
        self._stamp(user, current_user_id)
        self._commit()
        logger.info("Account unlocked: %s by user %s", user.username, current_user_id)
        return True

    def get_security_status(self, user_id: UUID) -> dict[str, Any]:
        """Security status (admins only)."""
        user = self._get_or_404(user_id)
        locked_until = user.locked_until
        return {
            "is_locked": locked_until is not None and locked_until > datetime.now(UTC),
            "failed_attempts": user.failed_login_attempts,
            "locked_until": locked_until,
            "last_login": user.last_login,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }
