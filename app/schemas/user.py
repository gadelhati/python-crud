# app/schemas/user.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=255)


class UserRequest(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    deleted_at: datetime | None
