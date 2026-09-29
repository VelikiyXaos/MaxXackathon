# services

from dataclasses import dataclass

from db.crud import admin as admin_crud
from db.crud import partner as partner_crud
from db.crud import student as student_crud
from . import session_scope


@dataclass
class UserProfile:
    """Профиль пользователя: его роль и отображаемое имя.

    display_name — фамилия и имя для учащегося, название компании
    для партнёра, None для администратора и незарегистрированных.
    """

    role: str | None
    display_name: str | None


async def get_user_profile(max_id: int) -> UserProfile:
    """Возвращает роль пользователя по его MAX id и его имя.

    Роль определяется в том же порядке, что и раньше: сначала
    администратор, затем учащийся, затем партнёр.
    """
    async with session_scope() as session:
        admin = await admin_crud.get_by_max_id(session, max_id)
        if admin is not None:
            return UserProfile(role="admin", display_name=None)

        student = await student_crud.get_by_max_id(session, max_id)
        if student is not None:
            name = f"{student.surname} {student.name}".strip()
            return UserProfile(
                role="student", display_name=name or None
            )

        partner = await partner_crud.get_by_max_id(session, max_id)
        if partner is not None:
            return UserProfile(
                role="partner", display_name=partner.name.strip() or None
            )

    return UserProfile(role=None, display_name=None)


async def get_user_role(max_id: int) -> str | None:
    """Возвращает роль пользователя по его MAX id или None."""
    return (await get_user_profile(max_id)).role


async def get_student(max_id: int):
    """Возвращает ученика по MAX id или None."""
    async with session_scope() as session:
        return await student_crud.get_by_max_id(session, max_id)


async def is_login_taken(login: str) -> bool:
    """Проверяет, занят ли логин другим учащимся."""
    async with session_scope() as session:
        return await student_crud.exists_by_login(session, login)


async def get_partner(max_id: int):
    """Возвращает партнёра по MAX id или None."""
    async with session_scope() as session:
        return await partner_crud.get_by_max_id(session, max_id)


async def get_admin(max_id: int):
    """Возвращает администратора по MAX id или None."""
    async with session_scope() as session:
        return await admin_crud.get_by_max_id(session, max_id)