from __future__ import annotations

from datetime import date
from typing import Any

from netschoolapi import NetSchoolAPI

from ABS_grade_provider import AbstractGradeProvider


class NetSchoolGradeProvider(AbstractGradeProvider):
    def __init__(
        self,
        *,
        client: NetSchoolAPI,
        today: date | None = None,
    ) -> None:
        super().__init__(today=today)
        self._client = client

    async def _fetch_grades(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[int]:
        diary = await self._client.diary(start=date_from, end=date_to)

        grades: list[int] = []
        for day in diary.schedule:
            if not (date_from <= day.day <= date_to):
                continue
            for lesson in day.lessons:
                for assignment in lesson.assignments:
                    grade = self._extract_mark(assignment)
                    if grade is not None:
                        grades.append(grade)
        return grades

    def _extract_mark(self, assignment: Any) -> int | None:
        mark = getattr(assignment, "mark", None)
        if mark is None:
            return None
        try:
            value = int(mark)
        except (TypeError, ValueError):
            return None
        return value if value in self.GRADE_TYPES else None