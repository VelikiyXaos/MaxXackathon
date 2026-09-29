from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Bonus


async def create(
    session: AsyncSession,
    *,
    name: str = "",
    promocode: str,
    need_experience: int,
    partner_id: int,
    end_date: date | None = None,
) -> Bonus:
    """Создаёт бонус и возвращает его"""
    bonus = Bonus(
        name=name,
        promocode=promocode,
        need_experience=need_experience,
        partner_id=partner_id,
        end_date=end_date,
    )
    session.add(bonus)
    await session.commit()
    await session.refresh(bonus)
    return bonus


async def get(session: AsyncSession, bonus_id: int) -> Bonus | None:
    """Возвращает бонус по id или None"""
    return await session.get(Bonus, bonus_id)


async def get_all(session: AsyncSession) -> list[Bonus]:
    """Возвращает список всех бонусов"""
    result = await session.execute(select(Bonus))
    return list(result.scalars())


async def get_by_partner(session: AsyncSession, partner_id: int) -> list[Bonus]:
    """Возвращает бонусы указанного партнёра"""
    result = await session.execute(
        select(Bonus).where(Bonus.partner_id == partner_id)
    )
    return list(result.scalars())


async def get_by_promocode(
    session: AsyncSession, promocode: str
) -> Bonus | None:
    """Возвращает бонус по промокоду или None"""
    result = await session.execute(
        select(Bonus).where(Bonus.promocode == promocode)
    )
    return result.scalars().first()


async def get_available(
    session: AsyncSession, experience: int, *, date_now: date | None = None
) -> list[Bonus]:
    """Возвращает бонусы, доступные при накопленном опыте"""
    timestamp = date_now or date.today()
    result = await session.execute(
        select(Bonus).where(
            Bonus.need_experience <= experience,
            (Bonus.end_date.is_(None)) | (Bonus.end_date >= timestamp),
        )
    )
    return list(result.scalars())


async def get_expired(
    session: AsyncSession, *, date_now: date | None = None
) -> list[Bonus]:
    """Возвращает бонусы с истёкшим сроком действия"""
    timestamp = date_now or date.today()
    result = await session.execute(
        select(Bonus).where(
            Bonus.end_date.is_not(None),
            Bonus.end_date < timestamp,
        )
    )
    return list(result.scalars())


async def update(
    session: AsyncSession,
    bonus_id: int,
    **fields: object,
) -> Bonus | None:
    """Обновляет указанные поля бонуса"""
    bonus = await session.get(Bonus, bonus_id)
    if bonus is None:
        return None
    for field, value in fields.items():
        setattr(bonus, field, value)
    await session.commit()
    await session.refresh(bonus)
    return bonus


async def delete(session: AsyncSession, bonus_id: int) -> bool:
    """Удаляет бонус по id, True если запись была"""
    bonus = await session.get(Bonus, bonus_id)
    if bonus is None:
        return False
    await session.delete(bonus)
    await session.commit()
    return True
