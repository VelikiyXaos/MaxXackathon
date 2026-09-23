# models

from sqlalchemy import ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Student(Base):
    """Ученик образовательного учреждения."""

    __tablename__ = "student"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    surname: Mapped[str] = mapped_column(String(255), nullable=False)
    patronymic: Mapped[str | None] = mapped_column(String(255))
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    student_group: Mapped[str] = mapped_column(String(255), nullable=False)
    max_id: Mapped[int] = mapped_column(Integer, nullable=False)
    login: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str | None] = mapped_column(String(255))
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    EI_id: Mapped[int] = mapped_column(
        ForeignKey("educational_institution.id"), nullable=False
    )

    institution: Mapped["EducationalInstitution"] = relationship(
        back_populates="students"
    )
    bonuses: Mapped[list["Bonus"]] = relationship(
        secondary="student_bonus", back_populates="students"
    )