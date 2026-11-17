# app/routers/auth.py - Router for handling authentication-related
# endpoints
from fastapi import APIRouter, status

from app.dependencies import DbSession
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.services.auth import ServiceAuth

auth = APIRouter(prefix="/login", tags=["Authentication"])


@auth.post("", response_model=TokenResponse)
def login(request: LoginRequest, db: DbSession) -> TokenResponse:
    return ServiceAuth(db).login(request.username, request.password)


@auth.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    return ServiceAuth(db).refresh(request.refresh_token)


@auth.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: RefreshTokenRequest, db: DbSession) -> None:
    ServiceAuth(db).logout(request.refresh_token)
