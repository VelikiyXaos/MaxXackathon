from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time

ASSIGNMENT_TYPES: dict[int, str] = {
    1: "Ответ на уроке",
    2: "Самостоятельная работа",
    3: "Контрольная работа",
    4: "Домашнее задание",
    5: "Практическая работа",
    6: "Лабораторная работа",
    7: "Тест",
    8: "Сочинение",
    9: "Реферат",
}

ASSIGNMENT_TYPE_IDS: dict[str, int] = {
    name: type_id for type_id, name in ASSIGNMENT_TYPES.items()
}

def _date_iso(value: date) -> str:
    """Отдаёт дату в формате ЭСУО"""
    return value.isoformat()


def _time_iso(value: time | None) -> str:
    """Отдаёт время в формате ЭСУО или пустую строку"""
    return value.strftime("%H:%M") if value is not None else ""


@dataclass
class Assignment:
    id: int
    comment: str
    type: str
    content: str
    mark: int | None
    is_duty: bool
    deadline: date

    def to_dict(self) -> dict:
        """Отдаёт задание в виде словаря"""
        return {
            "id": self.id,
            "comment": self.comment,
            "type": self.type,
            "content": self.content,
            "mark": self.mark,
            "is_duty": self.is_duty,
            "deadline": self.deadline,
        }

    def to_raw(self) -> dict:
        """Отдаёт задание в формате ответа ЭСУО"""
        raw: dict = {
            "id": self.id,
            "assignmentName": self.content,
            "typeId": ASSIGNMENT_TYPE_IDS.get(self.type, 4),
            "dueDate": f"{_date_iso(self.deadline)}T00:00:00",
        }
        if self.mark is not None or self.is_duty:
            raw["mark"] = {"mark": self.mark, "dutyMark": self.is_duty}
        else:
            raw["mark"] = None
        raw["markComment"] = {"name": self.comment} if self.comment else None
        return raw


@dataclass
class Lesson:
    day: date
    start: time
    end: time
    room: str
    number: int
    subject: str
    assignments: list[Assignment] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Отдаёт урок в виде словаря"""
        return {
            "day": self.day,
            "start": self.start,
            "end": self.end,
            "room": self.room,
            "number": self.number,
            "subject": self.subject,
            "assignments": [a.to_dict() for a in self.assignments],
        }

    def to_raw(self) -> dict:
        """Отдаёт урок в формате ответа ЭСУО"""
        return {
            "day": _date_iso(self.day),
            "startTime": _time_iso(self.start),
            "endTime": _time_iso(self.end),
            "room": self.room,
            "number": self.number,
            "subjectName": self.subject,
            "assignments": [a.to_raw() for a in self.assignments],
        }


@dataclass
class Day:
    lessons: list[Lesson]
    day: date

    def to_dict(self) -> dict:
        """Отдаёт день в виде словаря"""
        return {
            "lessons": [lesson.to_dict() for lesson in self.lessons],
            "day": self.day,
        }

    def to_raw(self) -> dict:
        """Отдаёт день в формате ответа ЭСУО"""
        return {
            "lessons": [lesson.to_raw() for lesson in self.lessons],
            "date": _date_iso(self.day),
        }


@dataclass
class Diary:
    start: date
    end: date
    schedule: list[Day]

    def to_dict(self) -> dict:
        """Отдаёт дневник в виде словаря"""
        return {
            "start": self.start,
            "end": self.end,
            "schedule": [day.to_dict() for day in self.schedule],
        }

    def to_raw(self) -> dict:
        """Отдаёт дневник в формате ответа ЭСУО"""
        return {
            "weekStart": _date_iso(self.start),
            "weekEnd": _date_iso(self.end),
            "weekDays": [day.to_raw() for day in self.schedule],
        }