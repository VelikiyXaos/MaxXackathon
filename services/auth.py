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
    async with session_scope() as session:
        for role, crud in _ROLE_CRUDS:
            if await crud.get_by_max_id(session, max_id) is not None:
                return role
    return None