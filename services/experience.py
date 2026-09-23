from db.crud import student as student_crud
from . import session_scope


async def calculate_and_save_school_experience(student_id: int, grades: dict[int, int]) -> int:
    """
    Пересчитывает суммарный опыт студента за оценки по школьной системе
    и записывает в БД.

    Семантика (по ТЗ):
        - опыт пересчитывается заново по всем оценкам, переданным в `grades`,
          и ЗАПИСЫВАЕТСЯ как абсолютное значение (не прибавляется);
        - провайдер оценок (`AbstractGradeProvider`) считает оценки только
          с 1 сентября текущего учебного года, поэтому 1 сентября опыт
          автоматически обнуляется;
        - ежедневный прогон в 00:00 идемпотентен: повторный вызов с теми же
          оценками не начисляет опыт повторно.

    Args:
        student_id: ID студента
        grades: Словарь с оценками, ключи - типы оценок (1,2,3,4,5), значения - их количество

    Returns:
        Изменение опыта (дельту): новое значение минус предыдущее.
        Отрицательное — опыт снизился (например, после 1 сентября).
    """
    xp_per_grade = {
        5: 50,
        4: 30,
        3: 10,
        2: -20,
        1: 0,
    }

    total_xp = sum(count * xp_per_grade.get(grade, 0) for grade, count in grades.items())

    async with session_scope() as session:
        student = await student_crud.get(session, student_id)
        if student is None:
            raise ValueError(f"Student with id {student_id} not found")
        delta = total_xp - student.experience
        student.experience = total_xp
        await session.commit()
        await session.refresh(student)

    return delta


def get_xp_for_level(level: int) -> int:
    """
    Возвращает количество опыта, необходимого для достижения уровня.

    Args:
        level: Номер уровня (0-15+)

    Returns:
        XP, необходимый для достижения данного уровня
    """
    if level <= 0:
        return 0
    if level > 15:
        level = 15
    return 100 * level * level + 50 * level


async def get_student_level_info(student_id: int) -> dict:
    """
    Возвращает информацию об уровне студента.

    Args:
        student_id: ID студента

    Returns:
        dict с полями:
            - current_level: текущий уровень (0-15)
            - xp_for_next_level: XP, необходимый для следующего уровня (цель)
            - progress_percent: прогресс внутри уровня в % (0.0-100.0)

    Raises:
        ValueError: если студент не найден
    """
    async with session_scope() as session:
        student = await student_crud.get(session, student_id)
        if student is None:
            raise ValueError(f"Student with id {student_id} not found")
        experience = student.experience

    # Находим текущий уровень
    current_level = 0
    for lvl in range(1, 16):
        if get_xp_for_level(lvl) <= experience:
            current_level = lvl
        else:
            break

    xp_start = get_xp_for_level(current_level)
    next_level = min(current_level + 1, 15)
    xp_end = get_xp_for_level(next_level)

    if current_level == 15:
        progress_percent = 100.0
    else:
        progress_percent = (experience - xp_start) / (xp_end - xp_start) * 100

    return {
        "current_level": current_level,
        "xp_for_next_level": xp_end,
        "progress_percent": round(progress_percent, 2),
    }