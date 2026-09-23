#crud

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Partner


async def create(
    session: AsyncSession,
    *,
    name: str,
    max_id: int,
) -> Partner:
    """Создаёт нового партнёра и возвращает его."""
    partner = Partner(name=name, max_id=max_id)
    session.add(partner)
    await session.commit()
    await session.refresh(partner)
    return partner


async def get(session: AsyncSession, partner_id: int) -> Partner | None:
    """Возвращает партнёра по id или None."""
    return await session.get(Partner, partner_id)


async def get_all(session: AsyncSession) -> list[Partner]:
    """Возвращает список всех партнёров."""
    result = await session.execute(select(Partner))
    return list(result.scalars())


async def update(
    session: AsyncSession,
    partner_id: int,
    **fields: object,
) -> Partner | None:
    """Обновляет указанные поля партнёра и возвращает его или None."""
    partner = await session.get(Partner, partner_id)
    if partner is None:
        return None
    for field, value in fields.items():
        setattr(partner, field, value)
    await session.commit()
    await session.refresh(partner)
    return partner


async def get_by_max_id(session: AsyncSession, max_id: int) -> Partner | None:
    """Возвращает партнёра по внешнему id (max_id) или None."""
    result = await session.execute(
        select(Partner).where(Partner.max_id == max_id)
    )
    return result.scalar_one_or_none()


async def delete(session: AsyncSession, partner_id: int) -> bool:
    """Удаляет партнёра по id. Возвращает True, если запись удалена."""
    partner = await session.get(Partner, partner_id)
    if partner is None:
        return False
    await session.delete(partner)
    await session.commit()
    return True