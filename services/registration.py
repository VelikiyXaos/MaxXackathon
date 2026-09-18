"""Регистрация ученика: подготовка данных, шифрование пароля и запись в БД.

Слой сервисов отделяет логику регистрации от бота: сюда приходят данные
об ученике, а наружу отдаётся сохранённая запись `Student`.

"""

from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass

from mock_egas.models import Diary
from mock_egas.scenarios import scenario
from sqlalchemy.exc import IntegrityError

from db.crud import student as student_crud
from db.models import Student

from . import session_scope
from .auth import is_student

logger = logging.getLogger(__name__)

#: Имя переменной окружения с ключом шифрования паролей.
ENCRYPTION_KEY_ENV = "EGAS_ENCRYPTION_KEY"


def _encryption_key() -> bytes:
    """Возвращает ключ шифрования паролей из окружения.
    """
    raw_key = os.getenv(ENCRYPTION_KEY_ENV)
    if not raw_key:
        raise RuntimeError(
            f"Переменная окружения {ENCRYPTION_KEY_ENV} не задана. "
            "Скопируйте .env.template в .env и укажите ключ шифрования "
            "паролей."
        )
    return raw_key.encode("utf-8")


def encrypt_password(password: str) -> str:
    """Обратимо шифрует пароль перед записью в БД.
    """
    if not password:
        raise ValueError("Пароль не может быть пустым")
    key = _encryption_key()
    data = password.encode("utf-8")
    cipher = bytes(value ^ key[i % len(key)] for i, value in enumerate(data))
    return base64.urlsafe_b64encode(cipher).decode("ascii")


def decrypt_password(secret: str) -> str:
    """Расшифровывает пароль, сохранённый методом `encrypt_password`.
    Корректный результат возможен только при том же ключе, которым было
    выполнено шифрование.
    """
    key = _encryption_key()
    try:
        cipher = base64.urlsafe_b64decode(secret.encode("ascii"))
    except ValueError as exc:
        raise ValueError(
            "Некорректный формат зашифрованного пароля"
        ) from exc
    data = bytes(value ^ key[i % len(key)] for i, value in enumerate(cipher))
    return data.decode("utf-8")


@dataclass
class StudentRegistrationData:
    """Данные об ученике, полученные от бота при регистрации."""

    name: str
    surname: str
    grade: int
    student_group: str
    max_id: int
    login: str
    EI_id: int
    patronymic: str | None = None
    password: str | None = None


def prepare_student_data(data: StudentRegistrationData) -> dict:
    """Подготавливает данные ученика для записи в БД.

    Проверяет обязательные поля, шифрует пароль (`encrypt_password`) и
    возвращает словарь, готовый к передаче в `student_crud.create`.
    """
    if not (data.name and data.surname and data.login and data.student_group):
        raise ValueError(
            "Обязательные поля (name, surname, login, student_group) "
            "не могут быть пустыми"
        )
    if data.max_id <= 0:
        raise ValueError("max_id должен быть положительным числом")
    if data.grade < 1 or data.grade > 11:
        raise ValueError("grade должен быть в диапазоне 1–11")

    return {
        "name": data.name,
        "surname": data.surname,
        "patronymic": data.patronymic,
        "grade": data.grade,
        "student_group": data.student_group,
        "max_id": data.max_id,
        "login": data.login,
        "EI_id": data.EI_id,
        "password": (
            encrypt_password(data.password) if data.password else None
        ),
    }


async def fetch_student_grades(student: Student) -> Diary:
    """Запрашивает данные об оценках ученика в ЭСУО после регистрации.
    Для разработки и тестов возвращается мок-сценарий из mock_egas;
    результат пока нигде не сохраняется.
    Параметр `student` сейчас не используется — он понадобится для
    авторизации в реальном клиенте ЭСУО.
    """
    # TODO: завести клиент netschoolapi и авторизоваться от имени ученика:
    #   client = netSchoolApiClient(...)          # не реализовано
    #   client.set_login(                         # не реализовано
    #       student.login, decrypt_password(student.password)
    #   )
    #   return await client.diary_for(student)    # не реализовано
    return scenario("regular_week")


async def register_student(data: StudentRegistrationData) -> Student:
    """Регистрирует ученика: готовит данные, пишет в БД, запрашивает оценки.

    1. Проверяет, что ученик ещё не зарегистрирован (по max_id);
    2. Шифрует пароль и сохраняет запись через `student_crud.create`;
    3. После записи вызывает `fetch_student_grades`.

    Сбой при запросе оценок не отменяет регистрацию: запись уже
    сохранена, ошибка логируется и подавляется.
    """
    if await is_student(data.max_id):
        raise ValueError(f"Ученик с max_id={data.max_id} уже зарегистрирован")

    prepared = prepare_student_data(data)

    try:
        async with session_scope() as session:
            student = await student_crud.create(session, **prepared)
    except IntegrityError:
        # Дубликат возможен при гонке: проверка is_student и create идут в
        # разных сессиях. Ловим при условии, что на max_id стоит UNIQUE.
        raise ValueError(
            f"Ученик с max_id={data.max_id} уже зарегистрирован"
        ) from None

    try:
        await fetch_student_grades(student)
    except Exception:
        logger.warning(
            "Не удалось получить оценки ученика max_id=%s; "
            "регистрация сохранена",
            data.max_id,
            exc_info=True,
        )

    return student