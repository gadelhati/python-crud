# app/main.py - Main application entry point for FastAPI, including
# router registration and application lifespan management
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers.auth import auth
from app.routers.base import base
from app.routers.user import user
from app.services.base import ServiceError


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Python Template", version="1.0.0", lifespan=lifespan)
app.include_router(base)
app.include_router(auth)
app.include_router(user)

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


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        root_path=settings.root_path,
        reload=settings.reload,
    )
