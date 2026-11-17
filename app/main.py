# app/main.py - Main application entry point for FastAPI, including
# router registration and application lifespan management
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import SessionLocal, engine
from app.models.base import Base
from app.routers.admin import admin
from app.routers.auth import auth
from app.routers.base import base
from app.routers.permission import permission
from app.routers.role import role
from app.routers.user import user
from app.services.base import ServiceError
from app.services.permission import ServicePermission


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Python Template", lifespan=lifespan)
app.include_router(admin)
app.include_router(base)
app.include_router(auth)
app.include_router(user)
app.include_router(role)
app.include_router(permission)

STATUS_BY_ERROR_CODE: dict[str, int] = {
    "not_found": status.HTTP_404_NOT_FOUND,
    "invalid_credentials": status.HTTP_401_UNAUTHORIZED,
    "token_expired": status.HTTP_401_UNAUTHORIZED,
    "invalid_token": status.HTTP_401_UNAUTHORIZED,
    "account_locked": status.HTTP_423_LOCKED,
    "conflict": status.HTTP_409_CONFLICT,
    "integrity_error": status.HTTP_409_CONFLICT,
    "validation_error": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "invalid_operation": status.HTTP_400_BAD_REQUEST,
}


@app.exception_handler(ServiceError)
def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    http_status = STATUS_BY_ERROR_CODE.get(exc.code, status.HTTP_400_BAD_REQUEST)
    headers = (
        {"WWW-Authenticate": "Bearer"} if http_status == status.HTTP_401_UNAUTHORIZED else None
    )
    return JSONResponse(
        status_code=http_status,
        content={"detail": exc.message, "code": exc.code},
        headers=headers,
    )


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    # Garante que as tabelas existem (opcional se você usa apenas Alembic)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        try:
            ServicePermission(db).sync_with_enum()
            db.commit()
            logger.info("Permissions synchronized with EnumPermissionAction.")
        except Exception:
            db.rollback()
            logger.exception("Failed to synchronize permissions on startup.")
            raise

    yield


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        root_path=settings.root_path,
        reload=settings.reload,
    )
