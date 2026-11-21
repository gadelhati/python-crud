# app/services/user.py - Service for handling user-related business logic,
#  including role management, password updates, and security status
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserPasswordRequest, UserRequest, UserResponse
from app.services.base import ServiceBase, ServiceError
from app.services.password import hash_password
from app.services.permission_policy import PermissionPolicy
from app.validations.user import UserValidation

logger = logging.getLogger(__name__)


class ServiceUser(ServiceBase[User, UserPasswordRequest, UserRequest, UserResponse]):
    """User service with user-specific rules."""

    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        super().__init__(db, self.users, UserResponse)

    def _resolve_roles(self, role_ids: list[UUID]) -> list:
        self._validate_ids(role_ids, UserValidation.MAX_ROLES_PER_USER, "roles")
        roles = self.roles.find_by_ids(role_ids)
        self._check_found(roles, role_ids, "roles")
        return list(roles)

    def create(self, dto: UserPasswordRequest, current_user_id: UUID | None = None) -> UserResponse:
        if self.users.find_by_username(dto.username, include_deleted=True) is not None:
            raise ServiceError("Username already registered", code="conflict")
        if self.users.find_by_email(dto.email, include_deleted=True) is not None:
            raise ServiceError("Email already registered", code="conflict")

        data = dto.model_dump(exclude_unset=True, exclude={"password", "role_ids"})
        user = User(**data, password=hash_password(dto.password))

        roles = self._resolve_roles(dto.role_ids) if dto.role_ids else self.roles.find_defaults()

        PermissionPolicy.ensure_can_assign_roles(
            self.db,
            current_user_id,
            roles,
        )

        user.roles = roles

        self._stamp(user, current_user_id, created=True)
        self.users.save(user)
        return self._to_dto(user)

    def update(
        self, id: UUID, dto: UserRequest, current_user_id: UUID | None = None
    ) -> UserResponse:
        user = self._get_or_404(id)
        data = dto.model_dump(exclude_unset=True, exclude={"password", "role_ids"})

        if (
            "username" in data
            and data["username"] != user.username
            and self.users.find_by_username(data["username"], include_deleted=True) is not None
        ):
            raise ServiceError("Username already registered", code="conflict")

        if (
            "email" in data
            and data["email"] != user.email
            and self.users.find_by_email(data["email"], include_deleted=True) is not None
        ):
            raise ServiceError("Email already registered", code="conflict")

        for field, value in data.items():
            setattr(user, field, value)

        if "role_ids" in dto.model_fields_set:
            roles = self._resolve_roles(dto.role_ids) if dto.role_ids else []

            PermissionPolicy.ensure_can_assign_roles(
                self.db,
                current_user_id,
                roles,
            )

            user.roles = roles

        self._stamp(user, current_user_id)
        self.users.save(user)
        return self._to_dto(user)

    def get_by_email(self, email: str, include_deleted: bool = False) -> UserResponse | None:
        user = self.users.find_by_email(email, include_deleted=include_deleted)
        return self._to_dto(user) if user else None

    def get_by_username(self, username: str, include_deleted: bool = False) -> UserResponse | None:
        user = self.users.find_by_username(username, include_deleted=include_deleted)
        return self._to_dto(user) if user else None

    def update_roles(
        self, user_id: UUID, role_ids: list[UUID], current_user_id: UUID | None = None
    ) -> UserResponse:
        user = self._get_or_404(user_id)
        roles = self._resolve_roles(role_ids)

        PermissionPolicy.ensure_can_assign_roles(
            self.db,
            current_user_id,
            roles,
        )

        user.roles = roles
        self._stamp(user, current_user_id)
        self.users.save(user)
        return self._to_dto(user)

    def set_password(
        self, user_id: UUID, password: str, current_user_id: UUID | None = None
    ) -> bool:
        user = self._get_or_404(user_id)
        user.password = hash_password(password)
        self._stamp(user, current_user_id)
        self.users.save(user)
        return True

    def unlock_account(self, user_id: UUID, current_user_id: UUID | None = None) -> bool:
        """Manual unlock (admins only)."""
        user = self._get_or_404(user_id)
        user.failed_login_attempts = 0
        user.locked_until = None
        self._stamp(user, current_user_id)
        self.users.save(user)
        logger.info("Account unlocked: %s by user %s", user.username, current_user_id)
        return True

    def get_security_status(self, user_id: UUID) -> dict[str, Any]:
        """Security status (admins only)."""
        user = self._get_or_404(user_id)
        locked_until = user.locked_until
        if locked_until is not None and locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=UTC)
        return {
            "is_locked": locked_until is not None and locked_until > datetime.now(UTC),
            "failed_attempts": user.failed_login_attempts,
            "locked_until": locked_until,
            "last_login": user.last_login,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }

    def create_first_user(self, data: UserPasswordRequest) -> UserResponse:
        """Creates the first admin user. Transaction commit handled by get_db() dependency."""
        if self.repository.count() > 0:
            raise ServiceError("First user already exists.", "conflict")

        admin_role = self.db.query(Role).filter(Role.name == "admin").first()
        if admin_role is None:
            admin_role = Role(
                name="admin",
                description="System administrator",
                is_default=False,
                is_system=True,
            )
            self.db.add(admin_role)
            self.db.flush()

        user = User(
            username=data.username,
            email=data.email,
            password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            roles=[admin_role],
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return UserResponse.model_validate(user, from_attributes=True)
