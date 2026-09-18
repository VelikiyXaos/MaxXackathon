from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Application


async def create(
    session: AsyncSession,
    *,
    type: str,
    partner_name: str,
    description: str,
    contact_details: str,
) -> Application:
    """Создаёт новую заявку и возвращает её."""
    application = Application(
        type=type,
        partner_name=partner_name,
        description=description,
        contact_details=contact_details,
    )
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


async def get(session: AsyncSession, application_id: int) -> Application | None:
    """Возвращает заявку по id или None."""
    return await session.get(Application, application_id)


async def get_all(session: AsyncSession) -> list[Application]:
    """Возвращает список всех заявок."""
    result = await session.execute(select(Application))
    return list(result.scalars())


async def get_by_type(session: AsyncSession, type: str) -> list[Application]:
    """Возвращает заявки указанного типа."""
    result = await session.execute(
        select(Application).where(Application.type == type)
    )
    return list(result.scalars())


async def update(
    session: AsyncSession,
    application_id: int,
    **fields: object,
) -> Application | None:
    """Обновляет указанные поля заявки и возвращает её или None."""
    application = await session.get(Application, application_id)
    if application is None:
        return None
    for field, value in fields.items():
        setattr(application, field, value)
    await session.commit()
    await session.refresh(application)
    return application


async def delete(session: AsyncSession, application_id: int) -> bool:
    """Удаляет заявку по id. Возвращает True, если запись удалена."""
    application = await session.get(Application, application_id)
    if application is None:
        return False
    await session.delete(application)
    await session.commit()
    return True