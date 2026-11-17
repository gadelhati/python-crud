# app/routers/base.py - Router for handling base endpoints like
# health checks and root message
from fastapi import APIRouter

base = APIRouter(prefix="", tags=["Base"])


@base.get("/")
def hello() -> dict[str, str]:
    return {"message": "Hello, World!"}


@base.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
