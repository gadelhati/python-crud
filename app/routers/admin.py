# app/routers/admin.py - Router for initial system bootstrap
from fastapi import APIRouter, status
from sqlalchemy import select

from app.dependencies import DbSession
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserRequest, UserResponse
from app.services.base import ServiceError
from app.services.password import hash_password
from app.services.permission import ServicePermission

admin = APIRouter(prefix="/admin/init", tags=["Administration"])


@admin.post(
    "/create-first-user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize database with the first administrator user",
)
def create_first_user(request: UserRequest, db: DbSession) -> UserResponse:
    user_repo = UserRepository(db)
    if user_repo.count(include_deleted=True) > 0:
        raise ServiceError(
            "System is already initialized. First user already exists.",
            code="conflict",
        )

    # 1. Synchronizes all Enum permissions in the database
    ServicePermission(db).sync_with_enum()
    all_permissions = list(db.scalars(select(Permission)).all())

    # 2. Creates or retrieves the 'admin' role in the system with all permissions
    role_repo = RoleRepository(db)
    admin_role = role_repo.find_by_name("admin", include_deleted=True)
    if admin_role is None:
        admin_role = Role(
            name="admin",
            description="System administrator with full access",
            is_default=False,
            is_system=True,
            permissions=all_permissions,
        )
        role_repo.save(admin_role)

    # 3. Creates the first user already active, verified, and with the 'admin' role
    first_user = User(
        username=request.username,
        email=request.email,
        password=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        is_active=True,
        is_verified=True,
        roles=[admin_role],
    )
    user_repo.save(first_user)

    return UserResponse.model_validate(first_user, from_attributes=True)
