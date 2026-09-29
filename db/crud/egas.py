from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EGAS


async def create(
    session: AsyncSession,
    *,
    name: str,
    API_file: str,
) -> EGAS:
    """Создаёт ЭГАС и возвращает её"""
    egas = EGAS(name=name, API_file=API_file)
    session.add(egas)
    await session.commit()
    await session.refresh(egas)
    return egas


async def get(session: AsyncSession, egas_id: int) -> EGAS | None:
    """Возвращает ЭГАС по id или None"""
    return await session.get(EGAS, egas_id)


async def get_all(session: AsyncSession) -> list[EGAS]:
    """Возвращает список всех ЭГАС"""
    result = await session.execute(select(EGAS))
    return list(result.scalars())


async def get_by_name(session: AsyncSession, name: str) -> EGAS | None:
    """Возвращает ЭГАС по названию или None"""
    result = await session.execute(select(EGAS).where(EGAS.name == name))
    return result.scalars().first()


async def update(
    session: AsyncSession,
    egas_id: int,
    **fields: object,
) -> EGAS | None:
    """Обновляет указанные поля ЭГАС"""
    egas = await session.get(EGAS, egas_id)
    if egas is None:
        return None
    for field, value in fields.items():
        setattr(egas, field, value)
    await session.commit()
    await session.refresh(egas)
    return egas


async def delete(session: AsyncSession, egas_id: int) -> bool:
    """Удаляет ЭГАС по id, True если запись была"""
    egas = await session.get(EGAS, egas_id)
    if egas is None:
        return False
    await session.delete(egas)
    await session.commit()
    return True
