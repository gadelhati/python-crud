# app/models/system_state.py
# Model representing the application's initialization state.

from sqlalchemy import Boolean, CheckConstraint, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SystemState(Base):
    """Stores persistent application initialization state."""

    __tablename__ = "system_state"

    __table_args__ = (CheckConstraint("id = 1", name="ck_system_state_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    bootstrap_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
