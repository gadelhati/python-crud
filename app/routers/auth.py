# app/routers/auth.py - Router for handling authentication-related
# endpoints
from fastapi import APIRouter

from app.dependencies import DbSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import ServiceAuth

auth = APIRouter(prefix="/login", tags=["Authentication"])


@auth.post("", response_model=TokenResponse)
def login(request: LoginRequest, db: DbSession) -> TokenResponse:
    return ServiceAuth(db).login(request.username, request.password)
