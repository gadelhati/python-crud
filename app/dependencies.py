# app/dependencies.py - Dependency injection setup for FastAPI,
# including user repository and authentication dependencies
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.token import decode_access_token

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
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    repo: UserRepo,
) -> User:
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Autenticação obrigatória",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = decode_access_token(credentials.credentials)
    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Usuário não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


AuthenticatedUser = Annotated[User, Depends(get_authenticated_user)]


def _is_admin(user: User) -> bool:
    return any(role.name == "admin" for role in user.roles)


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
    """Allows access if the authenticated user owns the resource or is an admin."""
    if current_user.id != user_id and not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para modificar outro usuário.",
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
SelfOrAdminUser = Annotated[User, Depends(require_self_or_admin)]
