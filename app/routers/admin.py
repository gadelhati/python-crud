# app/routers/admin.py - Router for initial system bootstrap
from fastapi import APIRouter, Request, status

from app.config import settings
from app.dependencies import DbSession
from app.rate_limit import limiter
from app.schemas.user import UserPasswordRequest, UserResponse
from app.services.permission import ServicePermission
from app.services.user import ServiceUser

admin = APIRouter(prefix="/admin", tags=["Admin"])


@admin.post(
    "/init/create-first-user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.rate_limit_bootstrap)
def create_first_user(
    request: Request,
    payload: UserPasswordRequest,
    db: DbSession,
) -> UserResponse:
    ServicePermission(db).sync_with_enum()
    return ServiceUser(db).create_first_user(payload)
