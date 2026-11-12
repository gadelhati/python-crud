# app/dependencies.py
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository

DbSession = Annotated[Session, Depends(get_db)]


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


UserRepo = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_or_404(user_id: int, repo: UserRepo) -> User:
    user = repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User não encontrado")
    return user


CurrentUser = Annotated[User, Depends(get_user_or_404)]
