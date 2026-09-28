# models

from sqlalchemy import Column, ForeignKey, Table

from db.database import Base

EI_with_EGAS = Table(
    "EI_with_EGAS",
    Base.metadata,
    Column("EI_id", ForeignKey("educational_institution.id"), primary_key=True),
    Column("EGAS_id", ForeignKey("EGAS.id"), primary_key=True),
)

student_bonus = Table(
    "student_bonus",
    Base.metadata,
    Column("student_id", ForeignKey("student.id"), primary_key=True),
    # ON DELETE CASCADE: удаление бонуса само убирает все выдачи студентам,
    # связи не приходится чистить вручную (см. Bonus.students.passive_deletes)
    Column(
        "bonus_id",
        ForeignKey("bonus.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)