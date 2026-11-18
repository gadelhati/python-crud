# app/routers/user.py - Router for handling user-related endpoints
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    AdminUser,
    DbSession,
    require_permission,
    require_self_or_permission,
)
from app.enum.permission_action import EnumPermissionAction
from app.models.user import User
from app.schemas.user import (
    UserRequest,
    UserRequestWithoutPassword,
    UserResponse,
    UserResponseAudit,
)
from app.services.user import ServiceUser

user = APIRouter(prefix="/user", tags=["User"])


@user.get("/audit", response_model=list[UserResponseAudit])
def find_all_audit(
    _: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return ServiceUser(db).list_audit(UserResponseAudit, page=page, limit=limit)["items"]


@user.get("/audit/{user_id}", response_model=UserResponseAudit)
def find_by_id_audit(
    user_id: UUID,
    _: AdminUser,
    db: DbSession,
):
    return ServiceUser(db).get_audit(user_id, UserResponseAudit)


@user.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create(
    request: UserRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission(EnumPermissionAction.CREATE_USER))],
):
    return ServiceUser(db).create(request, current_user_id=current_user.id)


@user.get("", response_model=list[UserResponse])
def find_all(
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.READ_USER))],
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return ServiceUser(db).list(page=page, limit=limit)["items"]


@user.get("/{user_id}", response_model=UserResponse)
def find_by_id(
    user_id: UUID,
    _: Annotated[User, Depends(require_self_or_permission(EnumPermissionAction.READ_USER))],
    db: DbSession,
):
    return ServiceUser(db).get(user_id)


@user.put("/{user_id}", response_model=UserResponse)
def update(
    user_id: UUID,
    request: UserRequestWithoutPassword,
    current_user: Annotated[
        User, Depends(require_self_or_permission(EnumPermissionAction.UPDATE_USER))
    ],
    db: DbSession,
):
    return ServiceUser(db).update(user_id, request, current_user_id=current_user.id)


@user.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(
    user_id: UUID,
    current_user: Annotated[
        User, Depends(require_self_or_permission(EnumPermissionAction.DELETE_USER))
    ],
    db: DbSession,
):
    ServiceUser(db).soft_delete(user_id, current_user_id=current_user.id)


@user.delete("/{user_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_by_id(user_id: UUID, current_user: AdminUser, db: DbSession):
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administradores não podem excluir a própria conta permanentemente.",
        )
    ServiceUser(db).delete(user_id)


@user.patch("/{user_id}/restore", response_model=UserResponse)
def restore_by_id(user_id: UUID, current_user: AdminUser, db: DbSession):
    return ServiceUser(db).restore(user_id, current_user_id=current_user.id)


@user.get("/{user_id}/security")
def get_security_status(user_id: UUID, _: AdminUser, db: DbSession):
    return ServiceUser(db).get_security_status(user_id)


@user.patch("/{user_id}/unlock", status_code=status.HTTP_204_NO_CONTENT)
def unlock_account(user_id: UUID, current_user: AdminUser, db: DbSession):
    ServiceUser(db).unlock_account(user_id, current_user_id=current_user.id)
