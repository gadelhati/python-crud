# app/routers/auth.py - Authentication endpoints
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.dependencies import DbSession, oauth2_scheme
from app.rate_limit import limiter
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.auth import ServiceAuth
from app.services.password_reset import ServicePasswordReset

auth = APIRouter(prefix="/login", tags=["Authentication"])


@auth.post("", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_login)
def login(request: Request, payload: LoginRequest, db: DbSession) -> TokenResponse:
    return ServiceAuth(db).login(payload.username, payload.password)


@auth.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_refresh)
def refresh_token(request: Request, payload: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    return ServiceAuth(db).refresh(payload.refresh_token)


@auth.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshTokenRequest,
    db: DbSession,
    access_token: Annotated[str | None, Depends(oauth2_scheme)],
) -> None:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ServiceAuth(db).logout(access_token, payload.refresh_token)


@auth.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.rate_limit_password_reset)
def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    db: DbSession,
) -> dict[str, str]:
    message = ServicePasswordReset(db).request_reset(str(payload.email))
    return {"message": message}


@auth.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.rate_limit_password_reset)
def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirmRequest,
    db: DbSession,
) -> None:
    ServicePasswordReset(db).confirm_reset(
        payload.token,
        payload.new_password,
    )
