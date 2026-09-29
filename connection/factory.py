from __future__ import annotations

from connection.ABS_egas_connector import AbstractEgasConnector
from connection.registry import get_connector_class
from db.crud import egas as egas_crud
from db.crud import ei_with_egas as ei_with_egas_crud
from db.crud import student as student_crud
from services import crypto, session_scope


async def get_egas_connector(student_id: int) -> AbstractEgasConnector:
    """Собирает готовый к опросу коннектор ЭСУО для студента"""
    async with session_scope() as session:
        student = await student_crud.get(session, student_id)
        if student is None:
            raise ValueError(f"Student with id {student_id} not found")

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
        password = (
            crypto.decrypt(student.password) if student.password else None
        )
        return connector_cls(login=student.login, password=password)
