from datetime import date

from sqlalchemy import Date, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Bonus(Base):
    """Бонус от партнёра за накопленный опыт."""

    __tablename__ = "bonus"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    promocode: Mapped[str] = mapped_column(String(255), nullable=False)
    need_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partner.id"), nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)

    partner: Mapped["Partner"] = relationship(back_populates="bonuses")
    students: Mapped[list["Student"]] = relationship(
        secondary="student_bonus", back_populates="bonuses"
    )