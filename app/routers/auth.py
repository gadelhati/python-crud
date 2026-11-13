from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.dependencies import UserRepo
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import create_access_token
from app.services.password import verify_password

auth = APIRouter(prefix="/login", tags=["Authentication"])


@auth.post("", response_model=TokenResponse)
def login(request: LoginRequest, repo: UserRepo) -> TokenResponse:
    user = repo.find_by_username(request.username)
    if user is None or not verify_password(request.password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
