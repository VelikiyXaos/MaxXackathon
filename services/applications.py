# services

from db.crud import admin as admin_crud
from db.crud import application as application_crud
from . import session_scope

async def get_applications() -> list[dict]:
    """Возвращает список всех заявок партнёров."""
    async with session_scope() as session:
        applications = await application_crud.get_all(session)
    return [
        {
            "id": a.id,
            "type": a.type,
            "partner_name": a.partner_name,
            "description": a.description,
            "contact_details": a.contact_details,
        }
        for a in applications
    ]


async def accept_application(application_id: int) -> None:
    """Принимает заявку: создаёт партнёра и удаляет заявку.

    max_id для партнёра берётся из контактов, если там есть число,
    иначе используется 0.
    """
    from db.crud import partner as partner_crud

    async with session_scope() as session:
        application = await application_crud.get(session, application_id)
        if application is None:
            return

        # Пытаемся извлечь max_id из контактов
        max_id = 0
        digits = "".join(ch for ch in application.contact_details if ch.isdigit())
        if digits:
            max_id = int(digits)

        await partner_crud.create(
            session, name=application.partner_name, max_id=max_id
        )
        await application_crud.delete(session, application_id)


async def reject_application(application_id: int) -> None:
    """Отклоняет заявку (удаляет её)."""
    async with session_scope() as session:
        await application_crud.delete(session, application_id)


async def add_admin(max_id: int) -> bool:
    """Добавляет администратора. False, если уже существует."""
    async with session_scope() as session:
        existing = await admin_crud.get_by_max_id(session, max_id)
        if existing is not None:
            return False
        await admin_crud.create(session, max_id=max_id)
        return True