from db.crud import student as student_crud

from . import session_scope

MIN_LEVEL = 1
MAX_LEVEL = 15

XP_PER_GRADE = {
    5: 50,
    4: 30,
    3: 0,
    2: -30,
    1: -50,
}


def get_xp_for_level(level: int) -> int:
    """Возвращает порог опыта, с которого начинается уровень"""
    if level <= 0:
        return 0
    if level > MAX_LEVEL:
        level = MAX_LEVEL
    return 100 * level * level + 50 * level


def get_level_for_xp(experience: int) -> int:
    """Возвращает максимальный уровень, доступный при этом опыте"""
    current_level = 0
    for lvl in range(MIN_LEVEL, MAX_LEVEL + 1):
        if get_xp_for_level(lvl) > experience:
            break
        current_level = lvl
    return current_level


async def calculate_and_save_school_experience(
    student_id: int, grades: dict[int, int]
) -> int:
    """Пересчитывает суммарный опыт студента за оценки и возвращает дельту"""
    total_xp = sum(
        count * XP_PER_GRADE.get(grade, 0) for grade, count in grades.items()
    )

    async with session_scope() as session:
        student = await student_crud.get(session, student_id)
        if student is None:
            raise ValueError(f"Student with id {student_id} not found")

        delta = total_xp - student.experience
        student.experience = total_xp
        await session.commit()
        await session.refresh(student)

    return delta


async def get_student_level_info(student_id: int) -> dict:
    """Возвращает уровень студента и прогресс до следующего уровня"""
    async with session_scope() as session:
        student = await student_crud.get(session, student_id)
        if student is None:
            raise ValueError(f"Student with id {student_id} not found")
        experience = student.experience

    current_level = get_level_for_xp(experience)
    next_level = min(current_level + 1, MAX_LEVEL)
    xp_start = get_xp_for_level(current_level)
    xp_end = get_xp_for_level(next_level)

    if current_level == MAX_LEVEL:
        progress_percent = 100.0
    else:
        progress_percent = (experience - xp_start) / (xp_end - xp_start) * 100

    return {
        "current_level": current_level,
        "xp_for_next_level": xp_end,
        "progress_percent": round(progress_percent, 2),
    }
