# models

from sqlalchemy import Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Partner(Base):
    """Партнёр-компания, выдающая бонусы."""

    __tablename__ = "partner"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_id: Mapped[int] = mapped_column(Integer, nullable=False)

    bonuses: Mapped[list["Bonus"]] = relationship(back_populates="partner")