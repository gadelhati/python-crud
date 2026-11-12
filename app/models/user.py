# app/models/user.py
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import IdMixin, TimestampMixin


class User(IdMixin, TimestampMixin, Base):
    """User entity representing a user in the system."""

    __tablename__ = "users"

    titulo: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[str] = mapped_column(String(255))
    carga_horaria: Mapped[int]
    qtd_exercicios: Mapped[int]
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, titulo={self.titulo!r})"
