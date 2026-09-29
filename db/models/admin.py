# models

from sqlalchemy import Identity, Integer
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Admin(Base):
    """Администратор бота."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    max_id: Mapped[int] = mapped_column(Integer, nullable=False)