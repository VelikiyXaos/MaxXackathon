from sqlalchemy import Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Subject(Base):
    """Субъект РФ (регион)."""

    __tablename__ = "subject"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    cities: Mapped[list["City"]] = relationship(back_populates="subject")