# app/routers/role.py - Router for handling role-related endpoints
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import DbSession, require_permission
from app.enum.permission_action import EnumPermissionAction
from app.models.user import User
from app.schemas.role import RoleRequest, RoleResponse, RoleResponseAudit
from app.services.role import ServiceRole

role = APIRouter(prefix="/role", tags=["Role"])


@role.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create(
    request: RoleRequest,
    current_user: Annotated[User, Depends(require_permission(EnumPermissionAction.CREATE_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).create(request, current_user_id=current_user.id)


@role.get("", response_model=list[RoleResponse])
def find_all(
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.READ_ROLE))],
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return ServiceRole(db).list(page=page, limit=limit)["items"]


@role.get("/defaults", response_model=list[RoleResponse])
def find_defaults(
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.READ_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).get_default_roles()


@role.get("/{role_id}", response_model=RoleResponse)
def find_by_id(
    role_id: UUID,
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.READ_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).get(role_id)


@role.put("/{role_id}", response_model=RoleResponse)
def update(
    role_id: UUID,
    request: RoleRequest,
    current_user: Annotated[User, Depends(require_permission(EnumPermissionAction.UPDATE_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).update(role_id, request, current_user_id=current_user.id)


@role.patch("/{role_id}/permissions", response_model=RoleResponse)
def update_permissions(
    role_id: UUID,
    permission_ids: list[UUID],
    current_user: Annotated[User, Depends(require_permission(EnumPermissionAction.UPDATE_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).update_permissions(
        role_id, permission_ids, current_user_id=current_user.id
    )


@role.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(
    role_id: UUID,
    current_user: Annotated[User, Depends(require_permission(EnumPermissionAction.DELETE_ROLE))],
    db: DbSession,
):
    ServiceRole(db).soft_delete(role_id, current_user_id=current_user.id)


@role.delete("/{role_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_by_id(
    role_id: UUID,
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.DELETE_ROLE))],
    db: DbSession,
):
    ServiceRole(db).delete(role_id)


@role.patch("/{role_id}/restore", response_model=RoleResponse)
def restore_by_id(
    role_id: UUID,
    current_user: Annotated[User, Depends(require_permission(EnumPermissionAction.UPDATE_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).restore(role_id, current_user_id=current_user.id)


@role.get("/audit", response_model=list[RoleResponseAudit])
def find_all_audit(
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.READ_ROLE))],
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return ServiceRole(db).list(page=page, limit=limit)["items"]


@role.get("/audit/defaults", response_model=list[RoleResponseAudit])
def find_defaults_audit(
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.READ_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).get_default_roles()


@role.get("/audit/{role_id}", response_model=RoleResponseAudit)
def find_by_id_audit(
    role_id: UUID,
    _: Annotated[User, Depends(require_permission(EnumPermissionAction.READ_ROLE))],
    db: DbSession,
):
    return ServiceRole(db).get(role_id)
