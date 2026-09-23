"""Подбор провайдера оценок ЭСУО для студента.

`EGAS.API_file` — название класса-обработчика для конкретной ЭСУО (ЕГАС).
Классы-обработчики регистрируются в `_HANDLER_REGISTRY` ниже; по мере
появления новых ЭСУО реестр пополняется.
"""

from __future__ import annotations

from connection.ABS_grade_provider import AbstractGradeProvider
from connection.egas_client import NetSchoolClient
from connection.grade_provider_NetSchoolAPI import EgasGradeProvider
from db.crud import egas as egas_crud
from db.crud import ei_with_egas as ei_with_egas_crud
from db.crud import student as student_crud
from services import session_scope

# Реестр обработчиков ЭСУО: имя класса (EGAS.API_file) → класс клиента.
_HANDLER_REGISTRY: dict[str, type] = {
    "NetSchoolClient": NetSchoolClient,
}


def get_egas_handler(name: str) -> type:
    """
    Возвращает класс-обработчик ЭСУО по имени (EGAS.API_file).

    Args:
        name: Имя класса-обработчика, например "NetSchoolClient".

    Raises:
        ValueError: обработчик с таким именем не зарегистрирован.
    """
    handler = _HANDLER_REGISTRY.get(name)
    if handler is None:
        raise ValueError(
            f"Обработчик ЭСУО '{name}' не зарегистрирован в "
            f"connection.factory._HANDLER_REGISTRY "
            f"(доступные: {sorted(_HANDLER_REGISTRY)})"
        )
    return handler


async def get_grade_provider(student_id: int) -> AbstractGradeProvider:
    """
    Возвращает провайдер оценок для указанного студента.

    Логика (по схеме БД):
        1. Найти студента (db.crud.student.get) → его EI_id,
           login, password.
        2. Найти ЭГАС учреждения
           (db.crud.ei_with_egas.get_egas_ids_for_institution) —
           у учреждения ровно одна ЭГАС, поэтому берём единственную.
        3. Взять EGAS.API_file (db.crud.egas.get) — имя класса
           обработчика этой ЭСУО.
        4. Найти класс в реестре (get_egas_handler), создать клиент
           с кредами студента и обернуть в EgasGradeProvider.

    Args:
        student_id: ID студента в БД бота.

    Returns:
        Готовый к опросу провайдер оценок.

    Raises:
        ValueError: студент не найден, у учреждения не подключена ЭГАС
            или обработчик ЭСУО не зарегистрирован.
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

        handler_cls = get_egas_handler(egas.API_file)
        client = handler_cls(login=student.login, password=student.password)

    return EgasGradeProvider(client=client)
