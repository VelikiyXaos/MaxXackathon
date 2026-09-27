"""Демонстрационный коннектор ЭСУО: оценки из тестовых сценариев mock_egas.

Подключается штатно, без единой правки фабрики и реестра:

    python -m mock_egas demo on     # EGAS.API_file = 'MockEgasConnector'
    python -m mock_egas demo off    # вернуть NetSchoolConnector

Модуль лежит в `connection/connectors/`, поэтому `registry.load_connectors()`
подхватывает класс сам, а `connection.factory.get_egas_connector()` создаёт
его по строке из БД.

Как получаются «разные данные каждый день»:

* оценки детерминированы датой — один и тот же день всегда даёт один и тот
  же набор, поэтому ночной прогон в 00:00 идемпотентен (повторный запуск
  ничего не начисляет сверх нового);
* набор сценариев буднего дня меняется каждую неделю, поэтому в новый день
  опыт растёт, а в выходные (`week_without_lessons`) не меняется;
* период берётся из базового класса: 1 сентября → сегодняшний день, то есть
  с каждым днём в выдачу попадает новая порция оценок.

Логины/пароли не проверяются: фейковая ЭСУО не ходит в сеть.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import ClassVar

from connection.ABS_egas_connector import AbstractEgasConnector
from mock_egas import scenario

logger = logging.getLogger(__name__)

#: Сценарий выходных: уроков нет → новых оценок нет → опыт не растёт.
WEEKEND_SCENARIO = "week_without_lessons"

#: Сценарии-кандидаты. Сценарии `mock_egas` проверяют парсинг краевых
#: случаев, поэтому оценок в них немного: год оценок они не моделируют.
#: Коннектор берёт из сценария оценки ближайшего дня, где они есть, и
#: повторяет их по кругу — так будний день почти всегда приносит новые
#: оценки, а набор меняется каждую неделю (шаг ротации — неделя календаря).
CANDIDATE_SCENARIOS: tuple[str, ...] = (
    "regular_week",
    "graded_week",
    "multi_assignment_lesson",
    "duty_marks",
    "busy_week",
    "sparse_schedule",
    "single_school_day",
    "ungraded_week",
    "overdue_assignments",
    "extreme_times",
)

_POOL_CACHE: tuple[str, ...] | None = None
_MARKS_CACHE: dict[str, tuple[tuple[int, ...], ...]] = {}


def _marked_days(name: str) -> tuple[tuple[int, ...], ...]:
    """Оценки сценария, сгруппированные по дням недели (без пустых дней)."""
    cached = _MARKS_CACHE.get(name)
    if cached is not None:
        return cached
    per_weekday: list[list[int]] = [[] for _ in range(7)]
    for diary_day in scenario(name).schedule:
        weekday = diary_day.day.weekday()
        for lesson in diary_day.lessons:
            for assignment in lesson.assignments:
                if assignment.mark is not None:
                    per_weekday[weekday].append(assignment.mark)
    result = tuple(tuple(marks) for marks in per_weekday if marks)
    _MARKS_CACHE[name] = result
    return result


def _pool() -> tuple[str, ...]:
    """Сценарии, у которых есть хотя бы одна оценка."""
    global _POOL_CACHE
    if _POOL_CACHE is None:
        _POOL_CACHE = tuple(
            name for name in CANDIDATE_SCENARIOS if _marked_days(name)
        )
    return _POOL_CACHE


def scenario_for_day(day: date) -> str:
    """Имя сценария `mock_egas`, который отдаёт оценки за `day`."""
    if day.weekday() >= 5:
        return WEEKEND_SCENARIO
    pool = _pool()
    if not pool:
        return WEEKEND_SCENARIO
    return pool[(day.toordinal() // 7) % len(pool)]


def marks_for_day(day: date) -> list[int]:
    """Оценки, которые фейковая ЭСУО отдаёт за один день `day`."""
    if day.weekday() >= 5:
        return []
    days = _marked_days(scenario_for_day(day))
    if not days:
        return []
    return list(days[day.weekday() % len(days)])


class MockEgasConnector(AbstractEgasConnector):
    """ЭСУО-имитация на тестовых данных пакета `mock_egas`."""

    code = "MOCK"
    default_base_url = "mock://mock_egas"

    #: Подмена «сегодня» для всех новых коннекторов. Нужна симуляции
    #: нескольких ночей подряд (см. `mock_egas demo nights`).
    _today_override: ClassVar[date | None] = None

    @classmethod
    def set_today(cls, value: date | None) -> None:
        """Задать/сбросить общую подмену текущей даты (None — реальная)."""
        cls._today_override = value

    def __init__(
        self,
        *,
        login: str,
        password: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        today: date | None = None,
    ) -> None:
        super().__init__(
            login=login,
            password=password,
            base_url=base_url,
            timeout=timeout,
            today=today or self._today_override,
        )

    async def _authenticate(self) -> None:
        """Фейковая ЭСУО не требует входа."""

    async def _fetch_grades(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[int]:
        grades: list[int] = []
        day = date_from
        while day <= date_to:
            grades.extend(marks_for_day(day))
            day += timedelta(days=1)

        logger.info(
            "mock_egas: студент %s, период %s..%s, сценарий дня %s, "
            "оценок за период %s",
            student_id,
            date_from,
            date_to,
            scenario_for_day(date_to),
            len(grades),
        )
        return grades
