# app/dependencies.py - Dependency injection setup for FastAPI
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.enum.permission_action import EnumPermissionAction
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.base import ServiceError
from app.services.token import (
    decode_access_token_claims_with_version,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


UserRepo = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_or_404(user_id: UUID, repo: UserRepo) -> User:
    user = repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User não encontrado")
    return user


CurrentUser = Annotated[User, Depends(get_user_or_404)]

bearer_scheme = HTTPBearer(auto_error=False)


def get_authenticated_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id, jti, _, token_auth_version = decode_access_token_claims_with_version(token)

        from sqlalchemy import select

        from app.models.revoked_token import RevokedToken

        if db.scalar(select(RevokedToken.jti).where(RevokedToken.jti == jti)) is not None:
            raise ServiceError("Token has been revoked", code="invalid_token")

    except ServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = UserRepository(db).find_by_id(user_id)

    if user is None or not user.is_active or user.auth_version != token_auth_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo ou sessão inválida.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


AuthenticatedUser = Annotated[User, Depends(get_authenticated_user)]


def _is_admin(user: User) -> bool:
    return any(role.name == "admin" for role in user.roles if role.deleted_at is None)


def _has_permission(user: User, required_action: EnumPermissionAction) -> bool:
    if _is_admin(user):
        return True

    return any(
        permission.action == required_action
        for role in user.roles
        if role.deleted_at is None
        for permission in role.permissions
    )


def require_admin(current_user: AuthenticatedUser) -> User:
    """Allows access only to users with the 'admin' role."""
    if not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return current_user


def require_self_or_admin(
    user_id: Annotated[UUID, Path()],
    current_user: AuthenticatedUser,
) -> User:
    """Allows access if the user owns the resource or is an admin."""
    if current_user.id != user_id and not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para modificar outro usuário.",
        )
    return current_user


SelfOrAdminUser = Annotated[User, Depends(require_self_or_admin)]


def require_permission(required_action: EnumPermissionAction) -> Callable[[User], User]:
    """Factory dependency that validates the required permission."""

    def dependency(current_user: AuthenticatedUser) -> User:
        if not _has_permission(current_user, required_action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão necessária: {required_action.value}",
            )
        return current_user

    return dependency


def require_self_or_permission(
    required_action: EnumPermissionAction,
) -> Callable[[UUID, User], User]:
    """Allows access to the resource owner or a user with the required permission."""

    def dependency(
        user_id: Annotated[UUID, Path()],
        current_user: AuthenticatedUser,
    ) -> User:
        if current_user.id != user_id and not _has_permission(current_user, required_action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Access denied. Requires resource ownership or permission: "
                    f"{required_action.value}"
                ),
            )
        return current_user

    return dependency


AdminUser = Annotated[User, Depends(require_admin)]
