"""Тестовые данные ЭСУО «Сетевой город» для разработки и тестов.

Пакет содержит модели (`Diary`, `Day`, `Lesson`, `Assignment`),
повторяющие структуру одноимённых классов библиотеки netschoolapi,
и фиксированные тест-кейсы в `scenarios`.

Пример:
    from mock_egas import scenario

    diary = scenario("regular_week")

Запуск самопроверки всех сценариев:
    python -m mock_egas
"""

from mock_egas.models import (
    ASSIGNMENT_TYPE_IDS,
    ASSIGNMENT_TYPES,
    Assignment,
    Day,
    Diary,
    Lesson,
)

from mock_egas.scenarios import (
    SCENARIOS,
    WEEK_END,
    WEEK_START,
    count_days_with_lessons,
    scenario,
)

__all__ = [
    "ASSIGNMENT_TYPE_IDS",
    "ASSIGNMENT_TYPES",
    "Assignment",
    "Day",
    "Diary",
    "Lesson",
    "SCENARIOS",
    "WEEK_END",
    "WEEK_START",
    "count_days_with_lessons",
    "scenario",
]