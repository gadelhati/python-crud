# app/schemas/user.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    titulo: str
    descricao: str
    carga_horaria: int
    qtd_exercicios: int


class UserRequest(UserBase): ...


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
