# services

from db.crud import admin as admin_crud
from db.crud import partner as partner_crud
from db.crud import student as student_crud
from . import session_scope


_ROLE_CRUDS = (
    ("admin", admin_crud),
    ("student", student_crud),
    ("partner", partner_crud),
)


async def get_user_role(max_id: int) -> str | None:
    """Возвращает роль пользователя по его MAX id или None."""
    async with session_scope() as session:
        for role, crud in _ROLE_CRUDS:
            if await crud.get_by_max_id(session, max_id) is not None:
                return role
    return None


async def is_registered(max_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь (любая роль)."""
    return await get_user_role(max_id) is not None


async def get_student(max_id: int):
    """Возвращает ученика по MAX id или None."""
    async with session_scope() as session:
        return await student_crud.get_by_max_id(session, max_id)


async def get_partner(max_id: int):
    """Возвращает партнёра по MAX id или None."""
    async with session_scope() as session:
        return await partner_crud.get_by_max_id(session, max_id)


async def get_admin(max_id: int):
    """Возвращает администратора по MAX id или None."""
    async with session_scope() as session:
        return await admin_crud.get_by_max_id(session, max_id)