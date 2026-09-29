from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import aiohttp
from yarl import URL

from connection.ABS_egas_connector import AbstractEgasConnector
from connection.errors import (
    EgasAuthError,
    EgasError,
    EgasStudentNotFoundError,
)

logger = logging.getLogger(__name__)

SESSION_COOKIE = "NETSCHOOL_SESSIONID"

CHUNK_DAYS = 28


class NetSchoolConnector(AbstractEgasConnector):
    code = "NETSCHOOL"
    default_base_url = "https://netschool.app"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._session: aiohttp.ClientSession | None = None
        self._sid: str | None = None
        self._egas_student_id: int | None = None

    @property
    def is_logged_in(self) -> bool:
        """Авторизован ли коннектор в ЭСУО"""
        return self._sid is not None

    async def aclose(self) -> None:
        """Завершает сессию ЭСУО и закрывает HTTP-соединение"""
        await self._release()

    async def _authenticate(self) -> None:
        if not self._password:
            raise EgasAuthError(
                f"У ученика с логином {self._login} не задан пароль для ЭСУО"
            )

        data = await self._fetch_json(
            "POST",
            f"{self._base_url}/login",
            json={"username": self._login, "password": self._password},
        )

        if isinstance(data, dict) and data.get("error"):
            raise EgasAuthError(
                f"ЭСУО отклонила авторизацию {self._login}: "
                f"{data.get('error')} {data.get('message', '')}".strip()
            )

        sid = data.get("sid") if isinstance(data, dict) else None
        sid = sid or self._get_session().cookie_val(SESSION_COOKIE)

        if not sid:
            raise EgasAuthError(
                f"ЭСУО не вернула идентификатор сессии для {self._login}"
            )

        self._sid = str(sid)
        self._get_session().cookie_jar.update_cookies(
            {SESSION_COOKIE: self._sid}, URL(self._base_url)
        )
        logger.info("Авторизация в ЭСУО выполнена: %s", self._login)

    async def _release(self) -> None:
        """Закрывает сессию в ЭСУО и HTTP-соединение"""
        if self.is_logged_in:
            await self._logout()
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None
        self._sid = None
        self._egas_student_id = None

    async def _logout(self) -> None:
        """Закрывает сессию в ЭСУО, сетевые ошибки глотая"""
        self._sid = None
        self._egas_student_id = None

        if self._session is None or self._session.closed:
            return

        try:
            await self._fetch_json("POST", f"{self._base_url}/logout", json={})
        except EgasError as exc:
            logger.warning(
                "Не удалось завершить сессию ЭСУО %s: %s", self._login, exc
            )

    async def _fetch_grades(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[int]:
        week_days = await self._get_diary(
            student_id=student_id,
            date_from=date_from,
            date_to=date_to,
        )
        return self._parse_marks(week_days)

    async def _get_diary(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        """Забирает дневник за период списком дней с оценками"""
        if date_to < date_from:
            return []

        if not self.is_logged_in:
            await self._authenticate()

        egas_student_id = await self._resolve_student_id()
        logger.debug(
            "Запрос дневника ЭСУО %s: %s — %s (id бота %s)",
            self._login,
            date_from,
            date_to,
            student_id,
        )

        week_days: list[dict] = []
        seen_days: set[str] = set()

        chunk_start = date_from
        while chunk_start <= date_to:
            chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS - 1), date_to)
            for week in await self._fetch_diary_chunk(
                egas_student_id, chunk_start, chunk_end
            ):
                for day in week.get("weekDays") or []:
                    if not isinstance(day, dict):
                        continue
                    day_key = day.get("date")
                    if day_key is not None:
                        if day_key in seen_days:
                            continue
                        seen_days.add(day_key)
                    week_days.append(day)
            chunk_start = chunk_end + timedelta(days=1)

        return week_days

    @staticmethod
    def _parse_marks(week_days: list[dict]) -> list[int]:
        """Достаёт оценки из weekDays[].lessons[].assignments[].mark"""
        grades: list[int] = []

        for day in week_days:
            for lesson in day.get("lessons") or []:
                for assignment in lesson.get("assignments") or []:
                    mark = assignment.get("mark")
                    if mark is None:
                        continue
                    grade = mark.get("mark")
                    if grade is not None:
                        grades.append(grade)

        return grades

    def _get_session(self) -> aiohttp.ClientSession:
        """Отдаёт HTTP-сессию, создавая её при первом обращении"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                cookie_jar=aiohttp.CookieJar(unsafe=True),
            )
        return self._session

    async def _fetch_diary_chunk(
        self,
        egas_student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        """Делает один запрос student/diary за часть периода"""
        data = await self._fetch_json(
            "GET",
            f"{self._base_url}/student/diary",
            params={
                "student_id": str(egas_student_id),
                "from_date": date_from.isoformat(),
                "to_date": date_to.isoformat(),
            },
        )

        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [week for week in data if isinstance(week, dict)]
        raise EgasError(
            f"ЭСУО вернула неожиданный формат дневника: {type(data).__name__}"
        )

    async def _resolve_student_id(self) -> int:
        """Определяет внутренний id ученика в ЭСУО по текущему логину"""
        if self._egas_student_id is not None:
            return self._egas_student_id

        data = await self._fetch_json("GET", f"{self._base_url}/users/current")

        persons = data.get("persons") if isinstance(data, dict) else None
        for person in persons or []:
            egas_student_id = person.get("studentId")
            if egas_student_id:
                self._egas_student_id = int(egas_student_id)
                return self._egas_student_id

        raise EgasStudentNotFoundError(
            f"У логина {self._login} в ЭСУО нет ученического профиля"
        )

    async def _fetch_json(self, method: str, url: str, **kwargs: Any) -> Any:
        """Выполняет запрос и читает JSON, поднимая свои исключения"""
        session = self._get_session()
        try:
            async with session.request(method, url, **kwargs) as response:
                return await self._read_json(response)
        except EgasError:
            raise
        except (aiohttp.ClientError, TimeoutError) as exc:
            raise EgasError(f"Сбой связи с ЭСУО {self._base_url}: {exc}") from exc

    async def _read_json(self, response: aiohttp.ClientResponse) -> Any:
        """Читает JSON-ответ, поднимая понятные исключения"""
        if response.status in (401, 403):
            raise EgasAuthError(
                f"ЭСУО отклонила запрос ({response.status}) для {self._login}"
            )
        if response.status >= 400:
            raise EgasError(
                f"ЭСУО вернула HTTP {response.status} на {response.url}"
            )

        try:
            return await response.json(content_type=None)
        except (aiohttp.ClientError, ValueError) as exc:
            raise EgasError(
                f"Не удалось разобрать ответ ЭСУО {response.url}: {exc}"
            ) from exc
