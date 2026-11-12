# app/routers/base.py
from fastapi import APIRouter

base = APIRouter()


@base.get("/")
def hello() -> dict[str, str]:
    return {"message": "Hello, World!"}


@base.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
