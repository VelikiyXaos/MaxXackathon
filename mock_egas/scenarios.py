"""Фиксированные тест-кейсы ЭСУО.

Каждый сценарий — именованная функция, возвращающая готовый объект `Diary`
(классы `Diary`, `Day`, `Lesson`, `Assignment` из `mock_esuo.models`).

Все даты зафиксированы и не зависят от текущего дня:
неделя понедельник 2026-09-14 — воскресенье 2026-09-20.

Сценарии покрывают типовые ситуации электронного дневника:
обычная неделя, каникулы, праздничные дни, оценки/«н/а», просроченные
задания, уроки без кабинета, несколько заданий на урок и т.п.
"""

from __future__ import annotations

from datetime import date, time
from typing import Callable

from mock_egas.models import Assignment, Day, Diary, Lesson

WEEK_START: date = date(2026, 9, 14)  # понедельник
WEEK_END: date = date(2026, 9, 20)    # воскресенье

#: Типичные длительности уроков (7 смен).
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
    return Day(lessons=list(lessons), day=day)


def _diary(*days: Day) -> Diary:
    return Diary(start=WEEK_START, end=WEEK_END, schedule=list(days))


# ---------------------------------------------------------------------------
# Сценарии
# ---------------------------------------------------------------------------

def regular_week() -> Diary:
    """Обычная учебная неделя.

    Пять учебных дней, у части уроков есть задания с оценками и комментариями,
    выходные — без уроков. Базовая «здоровая» ситуация.
    """
    mon = WEEK_START
    monday_alg_homework = _assignment(101, "Параграф 12, упражнения 1–5", "Домашнее задание",
                      date(2026, 9, 15), mark=5, comment="Отлично")
    monday_rus_homework = _assignment(102, "Подготовиться к диктанту", "Домашнее задание",
                      date(2026, 9, 16))

    tuesday_alg_work = _assignment(201, "Разложение многочлена на множители",
                      "Самостоятельная работа", date(2026, 9, 17), mark=4,
                      comment="Есть недочёты")
    tuesday_geo_homework = _assignment(202, "Придумать 3 велосипедных маршрута",
                      "Домашнее задание", date(2026, 9, 18))

    wednesday_bio_test = _assignment(301, "Среды обитания организмов", "Тест",
                       date(2026, 9, 18), mark=3)
    wednesday_lit_essay = _assignment(302, "Эссе «Моя будущая профессия»", "Сочинение",
                       date(2026, 9, 21))

    return _diary(
        _day(mon,
             _lesson(mon, 1, "Алгебра", room="301", assignments=[monday_rus_homework]),
             _lesson(mon, 2, "Русский язык", room="204", assignments=[monday_alg_homework]),
             _lesson(mon, 3, "Биология", room="112", assignments=[wednesday_bio_test]),
             _lesson(mon, 4, "История", room="210"),
             _lesson(mon, 5, "Физическая культура", room="Спортзал")),
        _day(date(2026, 9, 15),
             _lesson(date(2026, 9, 15), 1, "Алгебра", room="301", assignments=[tuesday_alg_work]),
             _lesson(date(2026, 9, 15), 2, "География", room="118", assignments=[tuesday_geo_homework]),
             _lesson(date(2026, 9, 15), 3, "Литература", room="204"),
             _lesson(date(2026, 9, 15), 4, "Физика", room="305")),
        _day(date(2026, 9, 16),
             _lesson(date(2026, 9, 16), 1, "Информатика", room="314"),
             _lesson(date(2026, 9, 16), 2, "Английский язык", room="408"),
             _lesson(date(2026, 9, 16), 3, "Химия", room="302", assignments=[wednesday_lit_essay]),
             _lesson(date(2026, 9, 16), 4, "Обществознание", room="210")),
        _day(date(2026, 9, 17),
             _lesson(date(2026, 9, 17), 1, "Русский язык", room="204"),
             _lesson(date(2026, 9, 17), 2, "Алгебра", room="301"),
             _lesson(date(2026, 9, 17), 3, "Биология", room="112"),
             _lesson(date(2026, 9, 17), 4, "История", room="210")),
        _day(date(2026, 9, 18),
             _lesson(date(2026, 9, 18), 1, "Литература", room="204"),
             _lesson(date(2026, 9, 18), 2, "Физика", room="305"),
             _lesson(date(2026, 9, 18), 3, "География", room="118"),
             _lesson(date(2026, 9, 18), 4, "Физическая культура", room="Спортзал")),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def week_without_lessons() -> Diary:
    """Неделя без единого урока (каникулы, буквенные дни).

    Все семь дней пустые. Проверка, что обработчик корректно показывает
    «уроков нет» без падений.
    """
    return _diary(
        _day(date(2026, 9, 14)), _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)), _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)), _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def holiday_in_middle() -> Diary:
    """Праздничный день посреди недели.

    Среда (2026-09-16) — выходной: день без уроков, остальные будни учебные.
    Проверка, что расписание не «съезжает» и праздничный день корректно
    отображается.
    """
    mon = WEEK_START
    return _diary(
        _day(mon, _lesson(mon, 1, "Алгебра", room="301"),
             _lesson(mon, 2, "История", room="210")),
        _day(date(2026, 9, 15),
             _lesson(date(2026, 9, 15), 1, "Физика", room="305"),
             _lesson(date(2026, 9, 15), 2, "Русский язык", room="204")),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17),
             _lesson(date(2026, 9, 17), 1, "Биология", room="112"),
             _lesson(date(2026, 9, 17), 2, "География", room="118")),
        _day(date(2026, 9, 18),
             _lesson(date(2026, 9, 18), 1, "Химия", room="302"),
             _lesson(date(2026, 9, 18), 2, "Английский язык", room="408")),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def graded_week() -> Diary:
    """Неделя, где за каждое задание выставлена оценка (2–5).

    Полезно для проверки расчёта среднего балла и цветовой разметки оценок.
    """
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
    lessons = []
    for number, (subject, content) in enumerate(lesson_plan, start=1):
        lesson = _lesson(
            mon, number, subject,
            room=f"{300 + number}",
            assignments=[
                _assignment(400 + number, content, "Контрольная работа",
                            date(2026, 9, 15), mark=grades[number - 1],
                            comment="Проверено")
            ],
        )
        lessons.append(lesson)
    return _diary(
        _day(mon, *lessons),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def ungraded_week() -> Diary:
    """Все задания без оценок (учитель ещё не проверил).

    `mark=None`, `is_duty=False`. Проверка отображения «ожидает оценки».
    """
    mon = WEEK_START
    return _diary(
        _day(mon,
             _lesson(mon, 1, "Математика", room="301",
                     assignments=[
                         _assignment(500, "Задача 12 (а–в)", "Домашнее задание",
                                     date(2026, 9, 15))
                     ]),
             _lesson(mon, 2, "Русский язык", room="204",
                     assignments=[
                         _assignment(501, "Диктант", "Домашнее задание",
                                     date(2026, 9, 15))
                     ])),
        _day(date(2026, 9, 15),
             _lesson(date(2026, 9, 15), 1, "Биология", room="112"),
             _lesson(date(2026, 9, 15), 2, "История", room="210")),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def duty_marks() -> Diary:
    """Задания с «н/а» (не аттестован) — duty-оценка.

    `mark=None`, `is_duty=True`. Проверка отображения «н/а» как отдельного
    статуса, а не пустой оценки или «двойки».
    """
    mon = WEEK_START
    return _diary(
        _day(mon,
             _lesson(mon, 1, "Алгебра", room="301",
                     assignments=[
                         _assignment(600, "Контрольная работа №2",
                                     "Контрольная работа", date(2026, 9, 15),
                                     is_duty=True)
                     ]),
             _lesson(mon, 2, "Физика", room="305",
                     assignments=[
                         _assignment(601, "Лабораторная работа №3",
                                     "Лабораторная работа", date(2026, 9, 16),
                                     is_duty=True)
                     ])),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def overdue_assignments() -> Diary:
    """Просроченные задания: дедлайн раньше начала недели.

    Позволяет проверить признак «просрочено» (`deadline < today`): список
    должен совпадать с `overdue()` из netschoolapi (метод `student/diary`).
    """
    mon = WEEK_START
    return _diary(
        _day(mon,
             _lesson(mon, 1, "Литература", room="204",
                     assignments=[
                         _assignment(700, "Прочитать «Мёртвые души» (гл. 4)",
                                     "Домашнее задание", date(2026, 9, 13)),
                         _assignment(701, "Стихотворение наизусть",
                                     "Ответ на уроке", date(2026, 9, 12))
                     ]),
             _lesson(mon, 2, "География", room="118",
                     assignments=[
                         _assignment(702, "Контурная карта (Европа)",
                                     "Практическая работа", date(2026, 9, 11))
                     ])),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def lessons_without_room() -> Diary:
    """Уроки без кабинета (улица, спортзал без номера, экскурсия).

    `room=""` у части уроков. Проверка корректного вывода пустого кабинета.
    """
    mon = WEEK_START
    return _diary(
        _day(mon,
             _lesson(mon, 1, "Физическая культура"),
             _lesson(mon, 2, "ОБЖ", room=""),
             _lesson(mon, 3, "Алгебра", room="301"),
             _lesson(mon, 4, "Экскурсия в музей", room="")),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def multi_assignment_lesson() -> Diary:
    """Один урок с несколькими заданиями сразу.

    Например, после урока три домашних задания на разные даты и одна уже
    выставленная оценка. Проверка, что всё содержимое урока показывается.
    """
    mon = WEEK_START
    return _diary(
        _day(mon,
             _lesson(mon, 1, "Алгебра", room="301",
                     assignments=[
                         _assignment(800, "КР №1", "Контрольная работа",
                                     date(2026, 9, 14), mark=5,
                                     comment="Молодец!"),
                         _assignment(801, "Домашнее задание: №312",
                                     "Домашнее задание", date(2026, 9, 15)),
                         _assignment(802, "Домашнее задание: №313–315",
                                     "Домашнее задание", date(2026, 9, 16)),
                     ])),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def busy_week() -> Diary:
    """Максимально плотная неделя.

    Все семь дней, по семь уроков, у каждого урока хотя бы одно задание.
    Стрессовый тест на корректность отрисовки большого объёма данных.
    """
    subjects = [
        "Алгебра", "Русский язык", "Геометрия", "Физика",
        "История", "Биология", "Литература",
    ]
    days = []
    assignment_id = 900
    for offset in range(7):
        current_day = date(2026, 9, 14 + offset)
        lessons = []
        for number, subject in enumerate(subjects, start=1):
            assignment_id += 1
            lesson = _lesson(
                current_day, number, subject, room=f"{100 + number}",
                assignments=[
                    _assignment(assignment_id, "Изучить §" + str(number + 1),
                                "Домашнее задание", date(2026, 9, 16 + offset))
                ],
            )
            lessons.append(lesson)
        days.append(_day(current_day, *lessons))
    return _diary(*days)


def no_assignments_week() -> Diary:
    """Только расписание без единого задания.

    Проверка отображения предметов/времени/кабинетов при отсутствии
    домашних заданий и оценок.
    """
    mon = WEEK_START
    return _diary(
        _day(mon,
             _lesson(mon, 1, "Математика", room="301"),
             _lesson(mon, 2, "Русский язык", room="204"),
             _lesson(mon, 3, "Физкультура"),
             _lesson(mon, 4, "ИЗО", room="209")),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def sparse_schedule() -> Diary:
    """Расписание с «окнами»: пропущены номера уроков.

    Есть уроки 2, 3, 6 в один день — номера не идут подряд. Проверка, что
    логика сортировки/отображения не предполагает непрерывность номеров.
    """
    mon = WEEK_START
    return _diary(
        _day(mon,
             _lesson(mon, 2, "Английский язык", room="408"),
             _lesson(mon, 3, "Химия", room="302"),
             _lesson(mon, 6, "Классный час", room="301")),
        _day(date(2026, 9, 15),
             _lesson(date(2026, 9, 15), 1, "Физика", room="305"),
             _lesson(date(2026, 9, 15), 5, "Алгебра", room="301")),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def single_school_day() -> Diary:
    """Всего один учебный день за неделю.

    Например, сокращённая предпраздничная неделя. Проверка краевого случая
    «очень мало данных».
    """
    fri = date(2026, 9, 18)
    return _diary(
        _day(date(2026, 9, 14)),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(fri,
             _lesson(fri, 1, "Литература", room="204",
                     assignments=[
                         _assignment(850, "Пересказать биографию Тургенева",
                                     "Домашнее задание", date(2026, 9, 21))
                     ])),
        _day(date(2026, 9, 19)),
        _day(date(2026, 9, 20)),
    )


def extreme_times() -> Diary:
    """Крайние времена занятий.

    Первый урок начинается в 8:00, есть занятие, заканчивающееся в 19:00
    (вторая смена/факультатив). Проверка парсинга времени на границах.
    """
    sat = date(2026, 9, 19)
    return _diary(
        _day(date(2026, 9, 14),
             _lesson(date(2026, 9, 14), 1, "Алгебра", room="301")),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(sat,
             _lesson(sat, 1, "Факультатив по программированию", room="314",
                     start=time(17, 0), end=time(19, 0)),
             _lesson(sat, 2, "Шахматы", room="109",
                     start=time(19, 10), end=time(20, 0))),
        _day(date(2026, 9, 20),
             _lesson(date(2026, 9, 20), 1, "Подготовка к олимпиаде", room="314",
                     start=time(8, 0), end=time(8, 45))),
    )


def weekend_lessons() -> Diary:
    """Учебная суббота.

    Некоторые школы учатся по субботам: в выходной день есть уроки.
    Проверка, что суббота/воскресенье показываются как полноценные дни.
    """
    sat = date(2026, 9, 19)
    return _diary(
        _day(date(2026, 9, 14)),
        _day(date(2026, 9, 15)),
        _day(date(2026, 9, 16)),
        _day(date(2026, 9, 17)),
        _day(date(2026, 9, 18)),
        _day(sat,
             _lesson(sat, 1, "Математика", room="301",
                     assignments=[
                         _assignment(999, "Олимпиадные задачи", "Домашнее задание",
                                     date(2026, 9, 21))
                     ]),
             _lesson(sat, 2, "Русский язык", room="204"),
             _lesson(sat, 3, "Физкультура")),
        _day(date(2026, 9, 20)),
    )


#: Реестр фиксированных тестовых случаев: имя -> фабрика `Diary`.
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
    """Вернуть имитацию дневника по имени тестового случая.

    Поднимает `KeyError`, если сценарий не найден.
    """
    try:
        factory = SCENARIOS[name]
    except KeyError:
        raise KeyError(
            f"Неизвестный сценарий {name!r}. "
            f"Доступные: {', '.join(SCENARIOS)}"
        ) from None
    return factory()


def count_days_with_lessons(diary: Diary) -> int:
    """Количество дней недели, в которых есть хотя бы один урок."""
    return sum(1 for day in diary.schedule if day.lessons)