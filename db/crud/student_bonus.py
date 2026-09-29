#crud

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.associations import student_bonus


async def add(
    session: AsyncSession,
    *,
    student_id: int,
    bonus_id: int,
) -> None:
    """Выдаёт бонус ученику."""
    await session.execute(
        student_bonus.insert().values(student_id=student_id, bonus_id=bonus_id)
    )
    await session.commit()


async def remove(session: AsyncSession, *, student_id: int, bonus_id: int) -> bool:
    """Отзывает бонус у ученика. True, если связь была удалена."""
    result = await session.execute(
        delete(student_bonus).where(
            student_bonus.c.student_id == student_id,
            student_bonus.c.bonus_id == bonus_id,
        )
    )
    await session.commit()
    return result.rowcount > 0


async def exists(session: AsyncSession, *, student_id: int, bonus_id: int) -> bool:
    """Проверяет, выдан ли бонус ученику."""
    result = await session.execute(
        select(student_bonus.c.student_id).where(
            student_bonus.c.student_id == student_id,
            student_bonus.c.bonus_id == bonus_id,
        )
    )
    return result.first() is not None


async def get_bonus_ids_for_student(
    session: AsyncSession, student_id: int
) -> list[int]:
    """Возвращает id всех бонусов, выданных ученику."""
    result = await session.execute(
        select(student_bonus.c.bonus_id).where(
            student_bonus.c.student_id == student_id
        )
    )
    return list(result.scalars())


async def get_student_ids_for_bonus(
    session: AsyncSession, bonus_id: int
) -> list[int]:
    """Возвращает id всех учеников, получивших бонус."""
    result = await session.execute(
        select(student_bonus.c.student_id).where(
            student_bonus.c.bonus_id == bonus_id
        )
    )
    return list(result.scalars())


async def count_students_for_bonus(session: AsyncSession, bonus_id: int) -> int:
    """Возвращает количество учеников, получивших бонус.

    Нужен, чтобы узнать размер каскадного удаления связей: после
    `DELETE FROM bonus` (FK ... ON DELETE CASCADE) сами строки
    `student_bonus` уже недоступны для подсчёта.
    """
    result = await session.execute(
        select(func.count())
        .select_from(student_bonus)
        .where(student_bonus.c.bonus_id == bonus_id)
    )
    return result.scalar_one()
