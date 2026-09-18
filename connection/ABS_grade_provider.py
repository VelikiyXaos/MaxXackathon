from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

GradesCount = dict[int, int]

class AbstractGradeProvider(ABC):
    """
    Абстрактный провайдер оценок учащегося. Позволяет получить количество 
    оценок за период с 1 сентября текущего уч.года до текущей даты.
    """

    GRADE_TYPES: tuple[int, ...] = (1, 2, 3, 4, 5)

    def __init__(self, *, today: date | None = None) -> None:
        # ДЛЯ ТЕСТИРОВАНИЯ : изменение "текущей даты"
        self._today = today or date.today()



    # Публичный API
    async def get_grades_count(
        self,
        *,
        student_id: int,
        today: date | None = None,
    ) -> GradesCount:
        """
        Возвращает словарь {тип_оценки: кол-во} за период с 1 сентября текущего 
        уч. года до текущей даты.

        param student_id: id ученика в БД бота
        param today: изм. текущей даты
        """

        current = today or self._today
        period_start, period_end = self._academic_year_period(current)

        raw_grades = self._fetch_grades(
            student_id=student_id,
            date_from=period_start,
            date_to=period_end,
        )

        return self._count_grades(raw_grades)


    #------------

    # Доп. методы
    @staticmethod
    def _academic_year_period(today: date) -> tuple[date, date]:
        """
        Границы текущего учебного года: с 1 сентября по текущую дату.

        * если сегодня [ДО 1го сентября), учебный год считается 
        начавшимся в прошлом году.
        """

        year = today.year if today.month >= 9 else today.year - 1
        start = date(year, 9, 1)
        return start, today

    def _count_grades(self, raw_grades: list[int]) -> GradesCount:
        """
        Делает из списка оценок в словарь {оценка: количество}.
        {0,0,0,0,0} - базово все будут нули
        """
        counts: GradesCount = {grade: 0 for grade in self.GRADE_TYPES}
        for grade in raw_grades:
            if grade in counts:
                counts[grade] += 1
        return counts

    @abstractmethod
    async def _fetch_grades(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[int]:
        """
        Получает список оценок за указанный период.
        """
        raise NotImplementedError