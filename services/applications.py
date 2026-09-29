from db.crud import admin as admin_crud
from db.crud import application as application_crud
from db.crud import partner as partner_crud

from . import session_scope


class AdminAddingError(Exception):
    def __init__(self, max_id: int) -> None:
        super().__init__(max_id)
        self.max_id = max_id


async def get_applications() -> list[dict]:
    """Возвращает список всех заявок партнёров"""
    async with session_scope() as session:
        applications = await application_crud.get_all(session)

    return [
        {
            "id": item.id,
            "max_id": item.max_id,
            "type": item.type,
            "partner_name": item.partner_name,
            "description": item.description,
            "contact_details": item.contact_details,
        }
        for item in applications
    ]


async def accept_application(application_id: int) -> None:
    """Принимает заявку: создаёт партнёра и удаляет заявку"""
    async with session_scope() as session:
        application = await application_crud.get(session, application_id)
        if application is None:
            return

        await partner_crud.create(
            session, name=application.partner_name, max_id=application.max_id
        )
        await application_crud.delete(session, application_id)


async def reject_application(application_id: int) -> None:
    """Отклоняет заявку, просто удаляя её"""
    async with session_scope() as session:
        await application_crud.delete(session, application_id)


async def add_admin(max_id: int) -> None:
    """Добавляет администратора, если он ещё не заведён"""
    async with session_scope() as session:
        if await admin_crud.get_by_max_id(session, max_id) is not None:
            raise AdminAddingError(max_id)
        await admin_crud.create(session, max_id=max_id)
