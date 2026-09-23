#crud

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.associations import EI_with_EGAS


async def add(
    session: AsyncSession,
    *,
    EI_id: int,
    EGAS_id: int,
) -> None:
    """Связывает образовательное учреждение с ЭГАС."""
    await session.execute(
        EI_with_EGAS.insert().values(EI_id=EI_id, EGAS_id=EGAS_id)
    )
    await session.commit()


async def remove(session: AsyncSession, *, EI_id: int, EGAS_id: int) -> bool:
    """Разрывает связь учреждения с ЭГАС. True, если связь была удалена."""
    result = await session.execute(
        delete(EI_with_EGAS).where(
            EI_with_EGAS.c.EI_id == EI_id,
            EI_with_EGAS.c.EGAS_id == EGAS_id,
        )
    )
    await session.commit()
    return result.rowcount > 0


async def exists(session: AsyncSession, *, EI_id: int, EGAS_id: int) -> bool:
    """Проверяет наличие связи между учреждением и ЭГАС."""
    result = await session.execute(
        select(EI_with_EGAS.c.EI_id).where(
            EI_with_EGAS.c.EI_id == EI_id,
            EI_with_EGAS.c.EGAS_id == EGAS_id,
        )
    )
    return result.first() is not None


async def get_egas_ids_for_institution(
    session: AsyncSession, EI_id: int
) -> list[int]:
    """Возвращает id всех ЭГАС, подключённых к учреждению."""
    result = await session.execute(
        select(EI_with_EGAS.c.EGAS_id).where(EI_with_EGAS.c.EI_id == EI_id)
    )
    return list(result.scalars())


async def get_institution_ids_for_egas(
    session: AsyncSession, EGAS_id: int
) -> list[int]:
    """Возвращает id всех учреждений, использующих ЭГАС."""
    result = await session.execute(
        select(EI_with_EGAS.c.EI_id).where(EI_with_EGAS.c.EGAS_id == EGAS_id)
    )
    return list(result.scalars())