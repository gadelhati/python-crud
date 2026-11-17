# app/routers/permission.py - Router for handling permission-related endpoints (read-only)
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.dependencies import AuthenticatedUser, DbSession
from app.enum.permission_action import EnumPermissionAction
from app.schemas.permission import PermissionResponse
from app.services.permission import ServicePermission

permission = APIRouter(prefix="/permission", tags=["Permission"])


@permission.get("", response_model=list[PermissionResponse])
def find_all(
    _: AuthenticatedUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return ServicePermission(db).list(page=page, limit=limit)["items"]


@permission.get("/by-action/{action}", response_model=list[PermissionResponse])
def find_by_action(
    action: EnumPermissionAction,
    _: AuthenticatedUser,
    db: DbSession,
):
    return ServicePermission(db).get_by_action(action)


@permission.get("/{permission_id}", response_model=PermissionResponse)
def find_by_id(permission_id: UUID, _: AuthenticatedUser, db: DbSession):
    return ServicePermission(db).get(permission_id)


@permission.post("/sync", status_code=status.HTTP_204_NO_CONTENT)
def sync_permissions(_: AuthenticatedUser, db: DbSession):
    ServicePermission(db).sync_with_enum()
