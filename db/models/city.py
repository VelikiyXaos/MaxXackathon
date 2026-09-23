# models

from sqlalchemy import ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class City(Base):
    """Город, привязанный к субъекту (региону) РФ."""

    __tablename__ = "city"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="cities")
    educational_institutions: Mapped[list["EducationalInstitution"]] = relationship(
        back_populates="city"
    )