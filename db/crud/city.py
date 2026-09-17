from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import City, Subject


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


async def get_subject_names_by_city_name(session: AsyncSession, city_name: str) -> list[str]:
    """Возвращает список названий регионов, в которых есть город с указанным названием."""
    result = await session.execute(
        select(Subject.name)
        .join(City, City.subject_id == Subject.id)
        .where(City.name == city_name)
        .distinct()
    )
    return [row[0] for row in result.fetchall()]