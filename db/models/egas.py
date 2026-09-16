from sqlalchemy import Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class EGAS(Base):
    """Электронная образовательная система (ЭГАС)."""

    __tablename__ = "EGAS"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    API_file: Mapped[str] = mapped_column(String(255), nullable=False)

    institutions: Mapped[list["EducationalInstitution"]] = relationship(
        secondary="EI_with_EGAS", back_populates="egas_systems"
    )