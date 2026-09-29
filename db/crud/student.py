#crud

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Student


async def create(
    session: AsyncSession,
    *,
    name: str,
    surname: str,
    grade: int,
    student_group: str,
    max_id: int,
    login: str,
    EI_id: int,
    patronymic: str | None = None,
    password: str | None = None,
    experience: int = 0,
) -> Student:
    """Создаёт нового ученика и возвращает его."""
    student = Student(
        name=name,
        surname=surname,
        patronymic=patronymic,
        grade=grade,
        student_group=student_group,
        max_id=max_id,
        login=login,
        password=password,
        experience=experience,
        EI_id=EI_id,
    )
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return student


async def get(session: AsyncSession, student_id: int) -> Student | None:
    """Возвращает ученика по id или None."""
    return await session.get(Student, student_id)


async def get_all(session: AsyncSession) -> list[Student]:
    """Возвращает список всех учеников."""
    result = await session.execute(select(Student))
    return list(result.scalars())


async def get_by_institution(
    session: AsyncSession, EI_id: int
) -> list[Student]:
    """Возвращает учеников указанного образовательного учреждения."""
    result = await session.execute(
        select(Student).where(Student.EI_id == EI_id)
    )
    return list(result.scalars())


async def get_by_login(session: AsyncSession, login: str) -> Student | None:
    """Возвращает ученика по логину или None."""
    result = await session.execute(
        select(Student).where(Student.login == login)
    )
    return result.scalar_one_or_none()


async def get_by_max_id(session: AsyncSession, max_id: int) -> Student | None:
    """Возвращает ученика по внешнему id (max_id) или None."""
    result = await session.execute(
        select(Student).where(Student.max_id == max_id)
    )
    return result.scalar_one_or_none()


async def update(
    session: AsyncSession,
    student_id: int,
    **fields: object,
) -> Student | None:
    """Обновляет указанные поля ученика и возвращает его или None."""
    student = await session.get(Student, student_id)
    if student is None:
        return None
    for field, value in fields.items():
        setattr(student, field, value)
    await session.commit()
    await session.refresh(student)
    return student


async def delete(session: AsyncSession, student_id: int) -> bool:
    """Удаляет ученика по id. Возвращает True, если запись удалена."""
    student = await session.get(Student, student_id)
    if student is None:
        return False
    await session.delete(student)
    await session.commit()
    return True


async def exists_by_max_id(session: AsyncSession, max_id: int) -> bool:
    """Проверяет, зарегистрирован ли ученик с таким max_id."""
    result = await session.execute(
        select(Student.id).where(Student.max_id == max_id)
    )
    return result.first() is not None


async def exists_by_login(session: AsyncSession, login: str) -> bool:
    """Проверяет, занят ли логин."""
    result = await session.execute(
        select(Student.id).where(Student.login == login)
    )
    return result.first() is not None