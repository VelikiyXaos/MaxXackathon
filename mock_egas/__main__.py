"""Самопроверка тестовых данных ЭСУО.

Запуск из корня проекта:

    python -m mock_esuo              # сводка + проверки инвариантов
    python -m mock_esuo --raw <имя>  # «сырой» JSON-ответ АПИ для сценария
    python -m mock_esuo --text <имя> # текстовое представление дневника

Проверки инвариантов повторяют ограничения схем netschoolapi:
- неделя фиксирована: понедельник 2026-09-14 — воскресенье 2026-09-20;
- в расписании ровно 7 дней без пропусков и дублей;
- дата урока совпадает с датой дня:
- время начала раньше времени окончания;
- номера уроков в дне уникальны;
- id заданий уникальны в пределах дневника;
- «н/а» (-is_duty=True) задание не имеет числовой оценки.

Функции `validate_diary` и `check_scenarios` можно использовать и из pytest:
    def test_all_scenarios():
        check_scenarios()
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta

from mock_esuo.models import Assignment, Day, Diary, Lesson
from mock_esuo.scenarios import SCENARIOS, WEEK_END, WEEK_START

#: Допустимые оценки (в «Сетевом городе» оценки 2–5, единица не ставится).
VALID_MARKS: set[int | None] = {None, 2, 3, 4, 5}


def validate_diary(diary: Diary, name: str = "diary") -> list[str]:
    """Проверка инвариантов тестовых данных. Возвращает список проблем."""
    problems: list[str] = []

    if diary.start != WEEK_START:
        problems.append(f"неверный день начала недели: {diary.start}")
    if diary.end != WEEK_END:
        problems.append(f"неверный день конца недели: {diary.end}")
    if WEEK_END - WEEK_START != timedelta(days=6):
        problems.append("неделя не укладывается в 7 дней")

    expected_dates = [
        WEEK_START + timedelta(days=offset) for offset in range(7)
    ]
    actual_dates = [day.day for day in diary.schedule]
    if actual_dates != expected_dates:
        problems.append(
            f"расписание не покрывает неделю целиком: {actual_dates}"
        )

    assignment_ids: dict[int, str] = {}
    for day in diary.schedule:
        lesson_numbers: set[int] = set()
        for lesson in day.lessons:
            if lesson.day != day.day:
                problems.append(
                    f"[{day.day}] урок №{lesson.number} {lesson.subject!r} "
                    f"относится к дате {lesson.day}"
                )
            if lesson.start >= lesson.end:
                problems.append(
                    f"[{day.day}] урок №{lesson.number} {lesson.subject!r}: "
                    f"время начала {lesson.start} >= конца {lesson.end}"
                )
            if lesson.number in lesson_numbers:
                problems.append(
                    f"[{day.day}] дублируется номер урока {lesson.number}"
                )
            lesson_numbers.add(lesson.number)

            for assignment in lesson.assignments:
                if assignment.id in assignment_ids:
                    problems.append(
                        f"id задания {assignment.id} используется дважды "
                        f"({assignment_ids[assignment.id]} и "
                        f"[{day.day} {lesson.subject!r}]"
                    )
                assignment_ids[assignment.id] = (
                    f"[{day.day} {lesson.subject!r}]"
                )
                if assignment.is_duty and assignment.mark is not None:
                    problems.append(
                        f"[{day.day}] задание {assignment.id} с «н/а» "
                        f"имеет оценку {assignment.mark}"
                    )
                if assignment.mark not in VALID_MARKS:
                    problems.append(
                        f"[{day.day}] задание {assignment.id} имеет "
                        f"некорректную оценку {assignment.mark!r}"
                    )
    return problems


def render_text(diary: Diary) -> str:
    """Компактное текстовое представление дневника."""
    lines = [f"Неделя: {diary.start} — {diary.end}"]
    for day in diary.schedule:
        if not day.lessons:
            lines.append(f"  {day.day}  (уроков нет)")
            continue
        lines.append(f"  {day.day}")
        for lesson in day.lessons:
            tasks = []
            for assignment in lesson.assignments:
                mark = ""
                if assignment.mark is not None:
                    mark = f" {assignment.mark}"
                elif assignment.is_duty:
                    mark = " н/а"
                elif assignment.deadline:
                    mark = f" до {assignment.deadline}"
                tasks.append(f"{assignment.content!r}{mark}")
            assignments = (
                ("; " + "; ".join(tasks)) if tasks else ""
            )
            lines.append(
                f"    {lesson.number}. {lesson.start:%H:%M}–{lesson.end:%H:%M} "
                f"{lesson.subject}"
                f"{(' (' + lesson.room + ')') if lesson.room else ''}"
                f"{assignments}"
            )
    return "\n".join(lines)


def check_scenarios() -> list[str]:
    """Проверка всех зарегистрированных сценариев."""
    failures: list[str] = []
    for name in SCENARIOS:
        try:
            diary = SCENARIOS[name]()
        except Exception as exc:  # pragma: no cover - ловится для отчёта
            failures.append(f"{name}: исключение при построении: {exc!r}")
            continue
        problems = validate_diary(diary, name)
        if problems:
            failures.append(f"{name}: " + "; ".join(problems))
    return failures


def _main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--raw":
        name = sys.argv[2]
        if name not in SCENARIOS:
            print(f"Неизвестный сценарий {name!r}", file=sys.stderr)
            return 2
        print(json.dumps(SCENARIOS[name]().to_raw(), ensure_ascii=False,
                         indent=2))
        return 0

    if len(sys.argv) >= 3 and sys.argv[1] == "--text":
        name = sys.argv[2]
        if name not in SCENARIOS:
            print(f"Неизвестный сценарий {name!r}", file=sys.stderr)
            return 2
        print(render_text(SCENARIOS[name]()))
        return 0

    header = f"{'Сценарий':<24} {'дней с уроками':<15} {'уроков':<8}{'заданий':<9}{'оценок':<8}статус"
    print(header)
    print("-" * len(header))
    total_lessons = 0
    total_assignments = 0
    total_marks = 0
    status_max = 0
    for name, factory in SCENARIOS.items():
        diary = factory()
        days_with = sum(1 for day in diary.schedule if day.lessons)
        lessons = sum(len(day.lessons) for day in diary.schedule)
        assignments = sum(
            len(lesson.assignments)
            for day in diary.schedule
            for lesson in day.lessons
        )
        marks = sum(
            1
            for day in diary.schedule
            for lesson in day.lessons
            for a in lesson.assignments
            if a.mark is not None
        )
        total_lessons += lessons
        total_assignments += assignments
        total_marks += marks
        problems = validate_diary(diary, name)
        status = "OK" if not problems else "ОШИБКА"
        status_max = max(status_max, len(problems))
        print(f"{name:<24} {days_with:<15} {lessons:<8}{assignments:<9}{marks:<8}{status}")
        for problem in problems:
            print(" " * 24 + "  ! " + problem)
    print("-" * len(header))
    print(f"Итого сценариев: {len(SCENARIOS)}, уроков: {total_lessons}, "
          f"заданий: {total_assignments}, оценок: {total_marks}")

    failures = check_scenarios()
    if failures:
        print("\nСЦЕНАРИИ НЕКОРРЕКТНЫ", file=sys.stderr)
        return 1
    print("\nВсе сценарии прошли проверку инвариантов.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())