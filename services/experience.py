from db.crud import student as student_crud
from . import session_scope


async def calculate_and_save_school_experience(student_id: int, grades: dict[int, int]) -> int:
    """
    Считает суммарный опыт за оценки по школьной системе и записывает в БД.

    Args:
        student_id: ID студента
        grades: Словарь с оценками, ключи - типы оценок (1,2,3,4,5), значения - их количество

    Returns:
        Начисленный опыт
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
        student.experience += total_xp
        await session.commit()
        await session.refresh(student)

    return total_xp


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
