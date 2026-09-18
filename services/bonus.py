from db.crud import bonus as bonus_crud
from db.crud import student as student_crud
from db.crud import student_bonus as student_bonus_crud
from db.models import Bonus
from . import session_scope


async def grant_available_bonuses(student_id: int) -> list[Bonus]:
    """Выдаёт ученику все доступные по опыту бонусы, которых у него ещё нет."""
    async with session_scope() as session:
        student = await student_crud.get(session, student_id)
        if student is None:
            return []

        available = await bonus_crud.get_available(session, student.experience)
        owned_ids = set(
            await student_bonus_crud.get_bonus_ids_for_student(session, student_id)
        )

        granted: list[Bonus] = []
        for bonus in available:
            if bonus.id in owned_ids:
                continue
            await student_bonus_crud.add(session, student_id=student_id, bonus_id=bonus.id)
            granted.append(bonus)
        return granted