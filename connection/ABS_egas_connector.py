"""Базовый класс коннектора к ЭСУО.

Коннектор — единственный класс, который знает про *свою* ЭСУО: адрес
сервера, маршруты логина, формат ответа с оценками. Всё, что одинаково у
любых ЭСУО, живёт здесь:

    * ученический год — период с 1 сентября по текущую дату;
    * подсчёт оценок {оценка: количество};
    * lifecycle (`async with` / `aclose`).

Как добавить новую ЭСУО
-----------------------
1. Положить файл в `connection/connectors/` с классом-наследником,
   реализующим `_authenticate()` и `_fetch_grades()`:

       class MySchoolConnector(AbstractEgasConnector):
           code = "MYSCHOOL"
           default_base_url = "https://journal.example.ru"

           async def _authenticate(self) -> None: ...
           async def _fetch_grades(self, *, student_id, date_from, date_to): ...

2. Вписать имя класса в `EGAS.API_file` для нужной ЭГАС (через бота или
   SQL). Реестр (`connection/registry.py`) сам подхватит новый файл при
   первом обращении — править существующий код не нужно.

3. Если у системы есть региональные серверы, адрес будет храниться в БД
   (`EGAS.base_url`); пока такой колонки нет, работает `default_base_url`
   класса, а явный `base_url` в конструкторе имеет приоритет.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import ClassVar

GradesCount = dict[int, int]


class AbstractEgasConnector(ABC):
    """Опрашивает ЭСУО об оценках одного ученика за текущий учебный год.

    Наследник отвечает только за свою ЭСУО: как войти и как из ответа
    получить список оценок. Публичный контракт (`get_grades_count`)
    одинаков для всех ЭСУО.
    """

    GRADE_TYPES: ClassVar[tuple[int, ...]] = (1, 2, 3, 4, 5)

    #: Короткий код ЭСУО. Работает как синоним имени класса в реестре,
    #: поэтому должен быть уникален во всём проекте. Планируется также
    #: колонка с адресом регионального сервера в таблице `EGAS`.
    code: ClassVar[str] = ""

    #: Адрес сервера по умолчанию. Региональные адреса будут храниться
    #: в БД (колонка `EGAS.base_url`); пока её нет — используется это
    #: значение, а явный `base_url` в конструкторе имеет приоритет.
    default_base_url: ClassVar[str] = ""

    def __init__(
        self,
        *,
        login: str,
        password: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        today: date | None = None,
    ) -> None:
        """
        Args:
            login: Логин ученика в ЭСУО.
            password: Пароль. Если пустой — опрос невозможен.
            base_url: Адрес сервера ЭСУО. Если не задан — берётся
                `default_base_url` класса.
            timeout: Таймаут одного HTTP-запроса, секунды.
            today: Фиксированная «текущая дата» (для тестов).
        """
        self._login = login
        self._password = password
        self._timeout = timeout
        # ДЛЯ ТЕСТИРОВАНИЯ: подмена текущей даты
        self._today = today or date.today()
        self._base_url = (base_url or self.default_base_url).rstrip("/")

    @property
    def login(self) -> str:
        return self._login

    @property
    def base_url(self) -> str:
        return self._base_url

    # -- Публичный API ------------------------------------------------------

    async def get_grades_count(
        self,
        *,
        student_id: int,
        today: date | None = None,
    ) -> GradesCount:
        """
        Возвращает {тип_оценки: кол-во} за период с 1 сентября текущего
        уч. года до текущей даты.

        Args:
            student_id: id ученика в БД бота.
            today: Переопределение «текущей даты» (тесты).
        """
        period_start, period_end = self._academic_year_period(today or self._today)
        raw_grades = await self._fetch_grades(
            student_id=student_id,
            date_from=period_start,
            date_to=period_end,
        )
        return self._count_grades(raw_grades)

    async def __aenter__(self) -> AbstractEgasConnector:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Освобождает внешние ресурсы коннектора (сессии, сокеты)."""
        await self._release()

    # -- Что реализует наследник -------------------------------------------

    @abstractmethod
    async def _authenticate(self) -> None:
        """
        Авторизует соединение с ЭСУО.

        Raises:
            EgasAuthError: нет пароля или сервер отклонил вход.
            EgasError: сервер недоступен.
        """

    @abstractmethod
    async def _fetch_grades(
        self,
        *,
        student_id: int,
        date_from: date,
        date_to: date,
    ) -> list[int]:
        """
        Возвращает список оценок за период — разбор формата своей ЭСУО.

        Raises:
            EgasAuthError: сессия протухла, нужна повторная авторизация.
            EgasError: ошибка сети или неожиданный формат ответа.
        """

    async def _release(self) -> None:
        """Завершает сессию ЭСУО, если она была открыта. По умолчанию ничего."""
        return None

    # -- Общая логика -------------------------------------------------------

    @staticmethod
    def _academic_year_period(today: date) -> tuple[date, date]:
        """
        Границы текущего учебного года: с 1 сентября по текущую дату.

        Если сегодня раньше 1 сентября, учебный год начался в прошлом году.
        """
        year = today.year if today.month >= 9 else today.year - 1
        return date(year, 9, 1), today

    def _count_grades(self, raw_grades: list[int]) -> GradesCount:
        """Список оценок → {оценка: количество} по GRADE_TYPES."""
        counts: GradesCount = {grade: 0 for grade in self.GRADE_TYPES}
        for grade in raw_grades:
            if grade in counts:
                counts[grade] += 1
        return counts
