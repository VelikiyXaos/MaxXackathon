from datetime import date

from connection.ABS_grade_provider import AbstractGradeProvider


class EgasGradeProvider(AbstractGradeProvider):
    def __init__(
        self,
        *,
        client,
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
        diary = await self._client.get_diary(
            student_id=student_id,
            date_from=date_from,
            date_to=date_to,
        )

        grades: list[int] = []

        for day in diary["weekDays"]:
            for lesson in day["lessons"]:
                for assignment in lesson["assignments"]:
                    mark = assignment.get("mark")

                    if mark is None:
                        continue

                    grade = mark.get("mark")

                    if grade is not None:
                        grades.append(grade)

        return grades