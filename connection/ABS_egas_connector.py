from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import ClassVar

GradesCount = dict[int, int]


class AbstractEgasConnector(ABC):
    GRADE_TYPES: ClassVar[tuple[int, ...]] = (1, 2, 3, 4, 5)

    code: ClassVar[str] = ""

    default_base_url: ClassVar[str] = ""

    def __init__(
        self,
        *,
        login: str,
        password: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        today: date | None = None,
    ) -> None:
        self._login = login
        self._password = password
        self._timeout = timeout
        self._today = today or date.today()
        self._base_url = (base_url or self.default_base_url).rstrip("/")

    @property
    def login(self) -> str:
        return self._login

    @property
    def base_url(self) -> str:
        return self._base_url

    async def get_grades_count(
        self,
        *,
        student_id: int,
        today: date | None = None,
    ) -> GradesCount:
        """Считает оценки с 1 сентября текущего учебного года по текущую дату"""
        period_start, period_end = self._academic_year_period(today or self._today)
        raw_grades = await self._fetch_grades(
            student_id=student_id,
            date_from=period_start,
            date_to=period_end,
        )
        return self._count_grades(raw_grades)

    async def __aenter__(self) -> AbstractEgasConnector:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Освобождает внешние ресурсы коннектора"""
        await self._release()

    @abstractmethod
    async def _authenticate(self) -> None:
        """Авторизует соединение с ЭСУО"""

    @abstractmethod
    async def _fetch_grades(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[int]:
        """Возвращает список оценок за период"""

    async def _release(self) -> None:
        """Закрывает сессию ЭСУО, если она была открыта"""

    @staticmethod
    def _academic_year_period(today: date) -> tuple[date, date]:
        """Отдаёт границы текущего учебного года: с 1 сентября по сегодня"""
        year = today.year if today.month >= 9 else today.year - 1
        return date(year, 9, 1), today

    def _count_grades(self, raw_grades: list[int]) -> GradesCount:
        """Собирает список оценок в словарь {оценка: количество}"""
        counts: GradesCount = {grade: 0 for grade in self.GRADE_TYPES}
        for grade in raw_grades:
            if grade in counts:
                counts[grade] += 1
        return counts
