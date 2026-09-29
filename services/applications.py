# services

from db.crud import admin as admin_crud
from db.crud import application as application_crud
from . import session_scope


class AdminAddingError(Exception):
    """Пользователь уже является администратором."""

    def __init__(self, max_id: int) -> None:
        super().__init__(max_id)
        self.max_id = max_id


async def get_applications() -> list[dict]:
    """Возвращает список всех заявок партнёров."""
    async with session_scope() as session:
        applications = await application_crud.get_all(session)
    return [
        {
            "id": a.id,
            "max_id": a.max_id,
            "type": a.type,
            "partner_name": a.partner_name,
            "description": a.description,
            "contact_details": a.contact_details,
        }
        for a in applications
    ]


async def accept_application(application_id: int) -> None:
    """Принимает заявку: создаёт партнёра и удаляет заявку."""
    from db.crud import partner as partner_crud

    async with session_scope() as session:
        application = await application_crud.get(session, application_id)
        if application is None:
            return

        await partner_crud.create(
            session, name=application.partner_name, max_id=application.max_id
        )
        await application_crud.delete(session, application_id)


async def reject_application(application_id: int) -> None:
    """Отклоняет заявку (удаляет её)."""
    async with session_scope() as session:
        await application_crud.delete(session, application_id)


async def add_admin(max_id: int) -> None:
    """Добавляет администратора.

    Raises:
        AdminAddingError: если пользователь уже является администратором.
    """
    async with session_scope() as session:
        if await admin_crud.get_by_max_id(session, max_id) is not None:
            raise AdminAddingError(max_id)
        await admin_crud.create(session, max_id=max_id)