#crud

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Admin


async def create(session: AsyncSession, *, max_id: int) -> Admin:
    """Создаёт нового администратора и возвращает его."""
    admin = Admin(max_id=max_id)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def get(session: AsyncSession, admin_id: int) -> Admin | None:
    """Возвращает администратора по id или None."""
    return await session.get(Admin, admin_id)


async def get_by_max_id(session: AsyncSession, max_id: int) -> Admin | None:
    """Возвращает администратора по внешнему id (max_id) или None."""
    result = await session.execute(
        select(Admin).where(Admin.max_id == max_id)
    )
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession) -> list[Admin]:
    """Возвращает список всех администраторов."""
    result = await session.execute(select(Admin))
    return list(result.scalars())


async def update(
    session: AsyncSession,
    admin_id: int,
    **fields: object,
) -> Admin | None:
    """Обновляет указанные поля администратора и возвращает его или None."""
    admin = await session.get(Admin, admin_id)
    if admin is None:
        return None
    for field, value in fields.items():
        setattr(admin, field, value)
    await session.commit()
    await session.refresh(admin)
    return admin


async def delete(session: AsyncSession, admin_id: int) -> bool:
    """Удаляет администратора по id. Возвращает True, если запись удалена."""
    admin = await session.get(Admin, admin_id)
    if admin is None:
        return False
    await session.delete(admin)
    await session.commit()
    return True