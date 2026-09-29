from __future__ import annotations

from datetime import date, time, timedelta
from typing import Callable

from mock_egas.models import Assignment, Day, Diary, Lesson

WEEK_START: date = date(2026, 9, 14)
WEEK_END: date = date(2026, 9, 20)

LESSON_TIMES: list[tuple[time, time]] = [
    (time(8, 0), time(8, 45)),
    (time(8, 55), time(9, 40)),
    (time(9, 50), time(10, 35)),
    (time(10, 55), time(11, 40)),
    (time(12, 0), time(12, 45)),
    (time(12, 55), time(13, 40)),
    (time(13, 50), time(14, 35)),
]


def _assignment(
    id_: int,
    content: str,
    type_: str,
    deadline: date,
    *,
    mark: int | None = None,
    is_duty: bool = False,
    comment: str = "",
) -> Assignment:
    """Собирает задание для сценария"""
    return Assignment(
        id=id_,
        comment=comment,
        type=type_,
        content=content,
        mark=mark,
        is_duty=is_duty,
        deadline=deadline,
    )


def _lesson(
    day: date,
    number: int,
    subject: str,
    *,
    room: str = "",
    start: time | None = None,
    end: time | None = None,
    assignments: list[Assignment] | None = None,
) -> Lesson:
    """Собирает урок, подставляя время по номеру из LESSON_TIMES"""
    if start is None or end is None:
        start, end = LESSON_TIMES[number - 1]
    return Lesson(
        day=day,
        start=start,
        end=end,
        room=room,
        number=number,
        subject=subject,
        assignments=assignments or [],
    )


def _day(day: date, *lessons: Lesson) -> Day:
    """Собирает день недели из уроков"""
    return Day(lessons=list(lessons), day=day)


def _week_days() -> tuple[date, ...]:
    """Отдаёт семь дат эталонной недели от понедельника до воскресенья"""
    return tuple(WEEK_START + timedelta(days=offset) for offset in range(7))


def _day_of_week(offset: int) -> date:
    """Отдаёт дату недели по смещению от её начала"""
    return WEEK_START + timedelta(days=offset)


def _week(*filled: Day) -> Diary:
    """Собирает дневник недели, ставя заполненные дни на свои даты"""
    by_date = {day.day: day for day in filled}
    schedule = [by_date.get(value, _day(value)) for value in _week_days()]
    return Diary(start=WEEK_START, end=WEEK_END, schedule=schedule)


def regular_week() -> Diary:
    """Строит учебную неделю с разбросанными по дням оценками"""
    mon, tue, wed, thu, fri = _week_days()[:5]

    tue_hw = _assignment(101, "Параграф 12, упражнения 1–5", "Домашнее задание",
                         date(2026, 9, 15), mark=5, comment="Отлично")
    mon_hw = _assignment(102, "Подготовиться к диктанту", "Домашнее задание",
                         date(2026, 9, 16))
    tue_work = _assignment(201, "Разложение многочлена на множители",
                           "Самостоятельная работа", date(2026, 9, 17), mark=4,
                           comment="Есть недочёты")
    tue_geo_hw = _assignment(202, "Придумать 3 велосипедных маршрута",
                             "Домашнее задание", date(2026, 9, 18))
    mon_test = _assignment(301, "Среды обитания организмов", "Тест",
                           date(2026, 9, 18), mark=3)
    wed_essay = _assignment(302, "Эссе «Моя будущая профессия»", "Сочинение",
                            date(2026, 9, 21))

    return _week(
        _day(mon,
             _lesson(mon, 1, "Алгебра", room="301", assignments=[mon_hw]),
             _lesson(mon, 2, "Русский язык", room="204", assignments=[tue_hw]),
             _lesson(mon, 3, "Биология", room="112", assignments=[mon_test]),
             _lesson(mon, 4, "История", room="210"),
             _lesson(mon, 5, "Физическая культура", room="Спортзал")),
        _day(tue,
             _lesson(tue, 1, "Алгебра", room="301", assignments=[tue_work]),
             _lesson(tue, 2, "География", room="118", assignments=[tue_geo_hw]),
             _lesson(tue, 3, "Литература", room="204"),
             _lesson(tue, 4, "Физика", room="305")),
        _day(wed,
             _lesson(wed, 1, "Информатика", room="314"),
             _lesson(wed, 2, "Английский язык", room="408"),
             _lesson(wed, 3, "Химия", room="302", assignments=[wed_essay]),
             _lesson(wed, 4, "Обществознание", room="210")),
        _day(thu,
             _lesson(thu, 1, "Русский язык", room="204"),
             _lesson(thu, 2, "Алгебра", room="301"),
             _lesson(thu, 3, "Биология", room="112"),
             _lesson(thu, 4, "История", room="210")),
        _day(fri,
             _lesson(fri, 1, "Литература", room="204"),
             _lesson(fri, 2, "Физика", room="305"),
             _lesson(fri, 3, "География", room="118"),
             _lesson(fri, 4, "Физическая культура", room="Спортзал")),
    )


def week_without_lessons() -> Diary:
    """Строит неделю без единого урока"""
    return _week()


def holiday_in_middle() -> Diary:
    """Строит неделю с выходным посередине"""
    mon, tue, thu, fri = (_day_of_week(i) for i in (0, 1, 3, 4))
    return _week(
        _day(mon,
             _lesson(mon, 1, "Алгебра", room="301"),
             _lesson(mon, 2, "История", room="210")),
        _day(tue,
             _lesson(tue, 1, "Физика", room="305"),
             _lesson(tue, 2, "Русский язык", room="204")),
        _day(thu,
             _lesson(thu, 1, "Биология", room="112"),
             _lesson(thu, 2, "География", room="118")),
        _day(fri,
             _lesson(fri, 1, "Химия", room="302"),
             _lesson(fri, 2, "Английский язык", room="408")),
    )


def graded_week() -> Diary:
    """Строит неделю, где за каждое задание выставлена оценка"""
    mon = WEEK_START
    grades = [5, 4, 3, 2, 5, 4]
    lesson_plan = [
        ("Алгебра", "Числовые неравенства"),
        ("Русский язык", "Причастие"),
        ("Биология", "Клеточное строение"),
        ("Физика", "Закон Ома"),
        ("История", "Крещение Руси"),
        ("Литература", "Лермонтов «Мцыри»"),
    ]
    lessons = [
        _lesson(
            mon,
            number,
            subject,
            room=f"{300 + number}",
            assignments=[
                _assignment(400 + number, content, "Контрольная работа",
                            date(2026, 9, 15), mark=grades[number - 1],
                            comment="Проверено")
            ],
        )
        for number, (subject, content) in enumerate(lesson_plan, start=1)
    ]
    return _week(_day(mon, *lessons))


def ungraded_week() -> Diary:
    """Строит неделю, где все задания без оценок"""
    mon, tue = _week_days()[:2]
    mon_math_hw = _assignment(500, "Задача 12 (а–в)", "Домашнее задание",
                              date(2026, 9, 15))
    mon_rus_hw = _assignment(501, "Диктант", "Домашнее задание",
                             date(2026, 9, 15))
    return _week(
        _day(mon,
             _lesson(mon, 1, "Математика", room="301",
                     assignments=[mon_math_hw]),
             _lesson(mon, 2, "Русский язык", room="204",
                     assignments=[mon_rus_hw])),
        _day(tue,
             _lesson(tue, 1, "Биология", room="112"),
             _lesson(tue, 2, "История", room="210")),
    )


def duty_marks() -> Diary:
    """Строит неделю с заданиями, отмеченными «н/а»"""
    mon = WEEK_START
    alg_duty = _assignment(600, "Контрольная работа №2", "Контрольная работа",
                           date(2026, 9, 15), is_duty=True)
    phys_lab = _assignment(601, "Лабораторная работа №3",
                           "Лабораторная работа", date(2026, 9, 16), is_duty=True)
    return _week(
        _day(mon,
             _lesson(mon, 1, "Алгебра", room="301", assignments=[alg_duty]),
             _lesson(mon, 2, "Физика", room="305", assignments=[phys_lab])),
    )


def overdue_assignments() -> Diary:
    """Строит неделю с просроченными заданиями"""
    mon = WEEK_START
    lit_hw = [
        _assignment(700, "Прочитать «Мёртвые души» (гл. 4)", "Домашнее задание",
                    date(2026, 9, 13)),
        _assignment(701, "Стихотворение наизусть", "Ответ на уроке",
                    date(2026, 9, 12)),
    ]
    geo_practice = _assignment(702, "Контурная карта (Европа)",
                               "Практическая работа", date(2026, 9, 11))
    return _week(
        _day(mon,
             _lesson(mon, 1, "Литература", room="204", assignments=lit_hw),
             _lesson(mon, 2, "География", room="118",
                     assignments=[geo_practice])),
    )


def lessons_without_room() -> Diary:
    """Строит неделю, где у уроков не указан кабинет"""
    mon = WEEK_START
    return _week(
        _day(mon,
             _lesson(mon, 1, "Физическая культура"),
             _lesson(mon, 2, "ОБЖ", room=""),
             _lesson(mon, 3, "Алгебра", room="301"),
             _lesson(mon, 4, "Экскурсия в музей", room="")),
    )


def multi_assignment_lesson() -> Diary:
    """Строит неделю с уроком, у которого сразу несколько заданий"""
    mon = WEEK_START
    alg_tasks = [
        _assignment(800, "КР №1", "Контрольная работа", date(2026, 9, 14),
                    mark=5, comment="Молодец!"),
        _assignment(801, "Домашнее задание: №312", "Домашнее задание",
                    date(2026, 9, 15)),
        _assignment(802, "Домашнее задание: №313–315", "Домашнее задание",
                    date(2026, 9, 16)),
    ]
    return _week(
        _day(mon,
             _lesson(mon, 1, "Алгебра", room="301", assignments=alg_tasks)),
    )


def busy_week() -> Diary:
    """Строит неделю, забитую уроками в каждый день"""
    subjects = [
        "Алгебра", "Русский язык", "Геометрия", "Физика",
        "История", "Биология", "Литература",
    ]
    days = []
    for offset, current_day in enumerate(_week_days()):
        lessons = [
            _lesson(
                current_day,
                number,
                subject,
                room=f"{100 + number}",
                assignments=[
                    _assignment(900 + offset * len(subjects) + number,
                                f"Изучить §{number + 1}",
                                "Домашнее задание",
                                date(2026, 9, 16 + offset))
                ],
            )
            for number, subject in enumerate(subjects, start=1)
        ]
        days.append(_day(current_day, *lessons))
    return _week(*days)


def no_assignments_week() -> Diary:
    """Строит неделю с расписанием, но без заданий"""
    mon = WEEK_START
    return _week(
        _day(mon,
             _lesson(mon, 1, "Математика", room="301"),
             _lesson(mon, 2, "Русский язык", room="204"),
             _lesson(mon, 3, "Физкультура"),
             _lesson(mon, 4, "ИЗО", room="209")),
    )


def sparse_schedule() -> Diary:
    """Строит неделю с пропущенными номерами уроков"""
    mon, tue = _week_days()[:2]
    return _week(
        _day(mon,
             _lesson(mon, 2, "Английский язык", room="408"),
             _lesson(mon, 3, "Химия", room="302"),
             _lesson(mon, 6, "Классный час", room="301")),
        _day(tue,
             _lesson(tue, 1, "Физика", room="305"),
             _lesson(tue, 5, "Алгебра", room="301")),
    )


def single_school_day() -> Diary:
    """Строит неделю с единственным учебным днём"""
    fri = _day_of_week(4)
    turgenev_hw = _assignment(850, "Пересказать биографию Тургенева",
                              "Домашнее задание", date(2026, 9, 21))
    return _week(
        _day(fri,
             _lesson(fri, 1, "Литература", room="204",
                     assignments=[turgenev_hw])),
    )


def extreme_times() -> Diary:
    """Строит неделю с занятиями на самых ранних и самых поздних часах"""
    mon, sat, sun = (_day_of_week(i) for i in (0, 5, 6))
    return _week(
        _day(mon, _lesson(mon, 1, "Алгебра", room="301")),
        _day(sat,
             _lesson(sat, 1, "Факультатив по программированию", room="314",
                     start=time(17, 0), end=time(19, 0)),
             _lesson(sat, 2, "Шахматы", room="109",
                     start=time(19, 10), end=time(20, 0))),
        _day(sun,
             _lesson(sun, 1, "Подготовка к олимпиаде", room="314",
                     start=time(8, 0), end=time(8, 45))),
    )


def weekend_lessons() -> Diary:
    """Строит неделю с учебной субботой"""
    sat = _day_of_week(5)
    olympiad_hw = _assignment(999, "Олимпиадные задачи", "Домашнее задание",
                              date(2026, 9, 21))
    return _week(
        _day(sat,
             _lesson(sat, 1, "Математика", room="301",
                     assignments=[olympiad_hw]),
             _lesson(sat, 2, "Русский язык", room="204"),
             _lesson(sat, 3, "Физкультура")),
    )


SCENARIOS: dict[str, Callable[[], Diary]] = {
    "regular_week": regular_week,
    "week_without_lessons": week_without_lessons,
    "holiday_in_middle": holiday_in_middle,
    "graded_week": graded_week,
    "ungraded_week": ungraded_week,
    "duty_marks": duty_marks,
    "overdue_assignments": overdue_assignments,
    "lessons_without_room": lessons_without_room,
    "multi_assignment_lesson": multi_assignment_lesson,
    "busy_week": busy_week,
    "no_assignments_week": no_assignments_week,
    "sparse_schedule": sparse_schedule,
    "single_school_day": single_school_day,
    "extreme_times": extreme_times,
    "weekend_lessons": weekend_lessons,
}


def scenario(name: str) -> Diary:
    """Отдаёт имитацию дневника по имени сценария"""
    try:
        factory = SCENARIOS[name]
    except KeyError:
        raise KeyError(
            f"Неизвестный сценарий {name!r}. "
            f"Доступные: {', '.join(SCENARIOS)}"
        ) from None
    return factory()


def count_days_with_lessons(diary: Diary) -> int:
    """Считает дни недели, в которых есть хотя бы один урок"""
    return sum(1 for day in diary.schedule if day.lessons)
