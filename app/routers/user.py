# app/routers/user.py
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession, UserRepo
from app.models.user import User
from app.schemas.user import UserRequest, UserResponse

user = APIRouter(prefix="/user", tags=["user"])


@user.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create(request: UserRequest, repo: UserRepo, db: DbSession):
    user = repo.save(User(**request.model_dump()))
    db.commit()
    return user


@user.get("", response_model=list[UserResponse])
def find_all(
    repo: UserRepo,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return repo.find_all(offset=offset, limit=limit)


@user.get("/{user_id}", response_model=UserResponse)
def find_by_id(user: CurrentUser):
    return user


@user.put("/{user_id}", response_model=UserResponse)
def update(request: UserRequest, user: CurrentUser, db: DbSession):
    for field, value in request.model_dump().items():
        setattr(user, field, value)
    db.commit()
    return user


@user.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(user_id: UUID, repo: UserRepo, db: DbSession):
    if not repo.delete_by_id(user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User não encontrado")
    db.commit()
