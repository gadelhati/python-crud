# app/routers/user.py
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import AuthenticatedUser, CurrentUser, DbSession, UserRepo
from app.models.user import User
from app.schemas.user import UserRequest, UserResponse
from app.services.password import hash_password

user = APIRouter(prefix="/user", tags=["user"])


@user.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create(request: UserRequest, repo: UserRepo):
    user = repo.save(
        User(
            username=request.username,
            email=request.email,
            password=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
        )
    )
    return user


@user.get("", response_model=list[UserResponse])
def find_all(
    repo: UserRepo,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return repo.find_all(offset=offset, limit=limit)


@user.get("/{user_id}", response_model=UserResponse)
def find_by_id(_: AuthenticatedUser, user: CurrentUser):
    return user


@user.put("/{user_id}", response_model=UserResponse)
def update(request: UserRequest, _: AuthenticatedUser, user: CurrentUser, db: DbSession):
    user.username = request.username
    user.email = request.email
    user.password = hash_password(request.password)
    user.first_name = request.first_name
    user.last_name = request.last_name
    return user


@user.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(user_id: UUID, _: AuthenticatedUser, repo: UserRepo, db: DbSession):
    if not repo.soft_delete_by_id(user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User não encontrado")


@user.delete("/{user_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_by_id(user_id: UUID, _: AuthenticatedUser, repo: UserRepo, db: DbSession):
    if not repo.delete_by_id(user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User não encontrado")


@user.patch("/{user_id}/restore", response_model=UserResponse)
def restore_by_id(user_id: UUID, _: AuthenticatedUser, repo: UserRepo, db: DbSession):
    user = repo.restore_by_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado ou não excluído")
    return user
