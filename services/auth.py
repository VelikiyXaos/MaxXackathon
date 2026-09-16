from db.crud import admin as admin_crud
from db.crud import partner as partner_crud
from db.crud import student as student_crud
from . import session_scope


async def is_student(max_id: int) -> bool:
    """Возвращает True, если ученик с указанным max_id существует."""
    async with session_scope() as session:
        student = await student_crud.get_by_max_id(session, max_id)
        return student is not None


async def is_partner(max_id: int) -> bool:
    """Возвращает True, если партнёр с указанным max_id существует."""
    async with session_scope() as session:
        partner = await partner_crud.get_by_max_id(session, max_id)
        return partner is not None


async def is_admin(max_id: int) -> bool:
    """Возвращает True, если администратор с указанным max_id существует."""
    async with session_scope() as session:
        admin = await admin_crud.get_by_max_id(session, max_id)
        return admin is not None