# services

from db.crud import student as student_crud
from . import session_scope
from .experience import get_student_level_info


async def get_student_progress(student_max_id: int) -> dict | None:
    """Возвращает прогресс ученика: опыт, уровень и заполнение шкалы.

    Сначала ученик находится по внешнему MAX id, а уровень считается
    по его внутреннему id — у get_student_level_info другой контракт.

    Returns:
        dict с полями experience, level, next_level, progress_percent.
        None, если ученик не найден.
    """
    async with session_scope() as session:
        student = await student_crud.get_by_max_id(session, student_max_id)
        if student is None:
            return None
        student_id = student.id
        experience = student.experience

    level_info = await get_student_level_info(student_id)

    return {
        "experience": experience,
        "level": level_info["current_level"],
        "next_level": level_info["xp_for_next_level"],
        "progress_percent": level_info["progress_percent"],
    }
