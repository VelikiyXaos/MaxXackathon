#crud

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import City


async def create(
    session: AsyncSession,
    *,
    name: str,
    subject_id: int,
) -> City:
    """Создаёт новый город и возвращает его."""
    city = City(name=name, subject_id=subject_id)
    session.add(city)
    await session.commit()
    await session.refresh(city)
    return city


async def get(session: AsyncSession, city_id: int) -> City | None:
    """Возвращает город по id или None."""
    return await session.get(City, city_id)


async def get_all(session: AsyncSession) -> list[City]:
    """Возвращает список всех городов."""
    result = await session.execute(select(City))
    return list(result.scalars())


async def get_by_subject(session: AsyncSession, subject_id: int) -> list[City]:
    """Возвращает города, привязанные к субъекту (региону)."""
    result = await session.execute(
        select(City).where(City.subject_id == subject_id)
    )
    return list(result.scalars())


async def update(
    session: AsyncSession,
    city_id: int,
    **fields: object,
) -> City | None:
    """Обновляет указанные поля города и возвращает его или None."""
    city = await session.get(City, city_id)
    if city is None:
        return None
    for field, value in fields.items():
        setattr(city, field, value)
    await session.commit()
    await session.refresh(city)
    return city


async def delete(session: AsyncSession, city_id: int) -> bool:
    """Удаляет город по id. Возвращает True, если запись удалена."""
    city = await session.get(City, city_id)
    if city is None:
        return False
    await session.delete(city)
    await session.commit()
    return True


async def search_by_name(
    session: AsyncSession, query: str, *, limit: int = 10
) -> list[City]:
    """Ищет города по подстроке в названии."""
    result = await session.execute(
        select(City)
        .where(City.name.ilike(f"%{query}%"))
        .limit(limit)
    )
    return list(result.scalars())