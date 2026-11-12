# app/main.py
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers.base import base
from app.routers.user import user


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Python Template", version="1.0.0", lifespan=lifespan)
app.include_router(base)
app.include_router(user, prefix="/api", tags=["Users"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        root_path=settings.root_path,
        reload=settings.reload,
    )
