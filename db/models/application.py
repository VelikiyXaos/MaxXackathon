# models

from sqlalchemy import Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Application(Base):
    """Заявка партнёра на подключение."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_details: Mapped[str] = mapped_column(String(255), nullable=False)