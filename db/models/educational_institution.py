from sqlalchemy import ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class EducationalInstitution(Base):
    """Образовательное учреждение."""

    __tablename__ = "educational_institution"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"), nullable=False)

    city: Mapped["City"] = relationship(back_populates="educational_institutions")
    egas_systems: Mapped[list["EGAS"]] = relationship(
        secondary="EI_with_EGAS", back_populates="institutions"
    )
    students: Mapped[list["Student"]] = relationship(back_populates="institution")