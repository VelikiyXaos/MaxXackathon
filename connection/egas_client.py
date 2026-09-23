"""Клиент ЭСУО «Сетевой город» (netschoolapi).

ПРОТОТИП — не реализован.
См. docs/Прототипы недостающих функций.md

Контракт клиента определяется тем, как его использует
connection.grade_provider_NetSchoolAPI.EgasGradeProvider:

    diary = await client.get_diary(
        student_id=..., date_from=..., date_to=...
    )
    # diary["weekDays"][i]["lessons"][j]["assignments"][k]["mark"]["mark"]
"""

from __future__ import annotations

from datetime import date


class NetSchoolClient:
    """Асинхронный клиент ЭСУО для одного студента."""

    def __init__(
        self,
        *,
        login: str,
        password: str | None = None,
    ) -> None:
        self._login = login
        self._password = password

    # -- lifecycle ---------------------------------------------------------

    async def login(self) -> None:
        """
        Авторизует сессию в ЭСУО (student.login / student.password).

        Raises:
            NotImplementedError: прототип, ещё не реализован.
        """
        raise NotImplementedError("Прототип: авторизация в ЭСУО (не реализовано)")

    async def logout(self) -> None:
        """Закрывает сессию в ЭСУО. Прототип."""
        raise NotImplementedError("Прототип: завершение сессии ЭСУО")

    # -- diary -------------------------------------------------------------

    async def get_diary(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> dict:
        """
        Возвращает дневник (raw-JSON в формате netschoolapi) за период.

        Args:
            student_id: ID студента в БД бота.
            date_from: Начало периода.
            date_to: Конец периода.

        Returns:
            dict с ключом "weekDays" — список дней с уроками и оценками.
            Структура соответствует mock_egas.models.Diary.to_raw().

        Raises:
            NotImplementedError: прототип, ещё не реализован.
        """
        raise NotImplementedError("Прототип: получение дневника из ЭСУО")
