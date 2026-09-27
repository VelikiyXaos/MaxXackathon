"""Подбор коннектора ЭСУО для студента.

Фабрика не знает ни про одну конкретную ЭСУО: по `EGAS.API_file` она
находит класс в реестре (`connection.registry`) и создаёт его с кредами
студента. Добавление новой ЭСУО не требует правок этого файла.
"""

from __future__ import annotations

from connection.ABS_egas_connector import AbstractEgasConnector
from connection.registry import get_connector_class
from db.crud import egas as egas_crud
from db.crud import ei_with_egas as ei_with_egas_crud
from db.crud import student as student_crud
from services import session_scope


async def get_egas_connector(student_id: int) -> AbstractEgasConnector:
    """
    Возвращает готовый к опросу коннектор ЭСУО для студента.

    Логика (по схеме БД):
        1. Найти студента → его EI_id, login, password.
        2. Найти ЭГАС учреждения (у учреждения ровно одна ЭГАС).
        3. Взять `EGAS.API_file` — имя класса коннектора этой ЭСУО.
        4. Создать коннектор из реестра с кредами студента.

    Args:
        student_id: ID студента в БД бота.

    Returns:
        Коннектор, готовый к `get_grades_count(...)`.

    Raises:
        ValueError: студент не найден, у учреждения не подключена ЭГАС
            или коннектор этой ЭСУО не зарегистрирован.
    """
    async with session_scope() as session:
        student = await student_crud.get(session, student_id)
        if student is None:
            raise ValueError(f"Student with id {student_id} not found")

        # У учреждения только одна ЭСУО (ЕГАС).
        egas_ids = await ei_with_egas_crud.get_egas_ids_for_institution(
            session, student.EI_id
        )
        if not egas_ids:
            raise ValueError(
                f"У учреждения {student.EI_id} не подключена ЭСУО (ЕГАС)"
            )
        egas = await egas_crud.get(session, egas_ids[0])
        if egas is None:
            raise ValueError(f"ЭСУО (ЕГАС) с id {egas_ids[0]} не найдена")

        connector_cls = get_connector_class(egas.API_file)
        return connector_cls(login=student.login, password=student.password)
