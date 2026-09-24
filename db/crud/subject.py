#crud

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import City, Subject


async def create(session: AsyncSession, *, name: str) -> Subject:
    """Создаёт новый субъект РФ и возвращает его."""
    subject = Subject(name=name)
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject


async def get(session: AsyncSession, subject_id: int) -> Subject | None:
    """Возвращает субъект РФ по id или None."""
    return await session.get(Subject, subject_id)


async def get_all(session: AsyncSession) -> list[Subject]:
    """Возвращает список всех субъектов РФ."""
    result = await session.execute(select(Subject))
    return list(result.scalars())


async def update(
    session: AsyncSession,
    subject_id: int,
    **fields: object,
) -> Subject | None:
    """Обновляет указанные поля субъекта РФ и возвращает его или None."""
    subject = await session.get(Subject, subject_id)
    if subject is None:
        return None
    for field, value in fields.items():
        setattr(subject, field, value)
    await session.commit()
    await session.refresh(subject)
    return subject


async def delete(session: AsyncSession, subject_id: int) -> bool:
    """Удаляет субъект РФ по id. Возвращает True, если запись удалена."""
    subject = await session.get(Subject, subject_id)
    if subject is None:
        return False
    await session.delete(subject)
    await session.commit()
    return True

async def search_by_city_name(
    session: AsyncSession, query: str, *, limit: int = 10
) -> list[Subject]:
    """Ищет регионы, в которых есть город с подстрокой в названии."""
    result = await session.execute(
        select(Subject)
        .join(City, City.subject_id == Subject.id)
        .where(City.name.ilike(f"%{query}%"))
        .distinct()
        .limit(limit)
    )
    return list(result.scalars())