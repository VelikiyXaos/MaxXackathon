from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import ClassVar

from connection.ABS_egas_connector import AbstractEgasConnector
from mock_egas import scenario

logger = logging.getLogger(__name__)

WEEKEND_SCENARIO = "week_without_lessons"

BASE_LOAD = 1
EXTRA_LOAD = 1
WEEK_STEP_LOAD = 1

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
_RUN_START: date | None = None


def set_run_start(value: date | None) -> None:
    """Задаёт или сбрасывает первую ночь симуляции обновлений"""
    global _RUN_START
    _RUN_START = value


def daily_load(day: date) -> int:
    """Отдаёт, во сколько раз фейковая ЭСУО выдаёт больше оценок в этот день

    Первая ночь симуляции даёт базовую нагрузку, каждая следующая — больше,
    а раз в неделю нагрузка растёт ещё на одну порцию. Дни до начала
    симуляции остаются базовыми, чтобы накопленный опыт не обнулялся.
    """
    if _RUN_START is None or day < _RUN_START:
        return BASE_LOAD
    passed = (day - _RUN_START).days
    if passed == 0:
        return BASE_LOAD
    return BASE_LOAD + EXTRA_LOAD + (passed - 1) // 7 * WEEK_STEP_LOAD


def _marked_days(name: str) -> tuple[tuple[int, ...], ...]:
    """Группирует оценки сценария по дням недели, пустые дни отбрасывая"""
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
    """Отдаёт сценарии, у которых есть хотя бы одна оценка"""
    global _POOL_CACHE
    if _POOL_CACHE is None:
        _POOL_CACHE = tuple(
            name for name in CANDIDATE_SCENARIOS if _marked_days(name)
        )
    return _POOL_CACHE


def scenario_for_day(day: date) -> str:
    """Выбирает сценарий mock_egas, который отдаёт оценки за этот день"""
    if day.weekday() >= 5:
        return WEEKEND_SCENARIO

    pool = _pool()
    if not pool:
        return WEEKEND_SCENARIO
    return pool[(day.toordinal() // 7) % len(pool)]


def marks_for_day(day: date) -> list[int]:
    """Отдаёт оценки фейковой ЭСУО за один день с учётом роста нагрузки"""
    if day.weekday() >= 5:
        return []

    days = _marked_days(scenario_for_day(day))
    if not days:
        return []
    return list(days[day.weekday() % len(days)]) * daily_load(day)


class MockEgasConnector(AbstractEgasConnector):
    code = "MOCK"
    default_base_url = "mock://mock_egas"

    _today_override: ClassVar[date | None] = None

    @classmethod
    def set_today(cls, value: date | None) -> None:
        """Задаёт или сбрасывает общую подмену текущей даты"""
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
        """Фейковая ЭСУО не требует входа"""

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
