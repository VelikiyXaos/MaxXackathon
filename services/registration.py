# services

from dataclasses import dataclass

from db.crud import city as city_crud
from db.crud import educational_institution as ei_crud
from db.crud import student as student_crud
from db.crud import subject as subject_crud
from . import session_scope


@dataclass
class SubjectCandidate:
    """Кандидат по поиску региона."""

    id_: int
    name: str


@dataclass
class CityCandidate:
    """Кандидат по поиску города/региона."""

    id_: int
    name: str


@dataclass
class InstitutionCandidate:
    """Кандидат по поиску образовательного учреждения."""

    id_: int
    name: str


class RegistrationError(Exception):
    """Ошибка регистрации с человекочитаемым сообщением."""


async def search_subjects_by_city(query: str) -> list[SubjectCandidate]:
    """Шаг 1: по названию города находит регионы, где такой город есть."""
    query = query.strip()
    if len(query) < 2:
        return []
    async with session_scope() as session:
        subjects = await subject_crud.search_by_city_name(session, query)
    return [SubjectCandidate(id_=s.id, name=s.name) for s in subjects]


async def search_cities_in_subject(
    subject_id: int, query: str
) -> list[CityCandidate]:
    """Шаг 2: внутри выбранного региона ищет города по подстроке."""
    query = query.strip()
    if len(query) < 2:
        return []
    async with session_scope() as session:
        cities = await city_crud.search_by_subject_and_name(
            session, subject_id, query
        )
    return [CityCandidate(id_=c.id, name=c.name) for c in cities]


async def search_institutions(query: str) -> list[InstitutionCandidate]:
    """Поиск образовательных учреждений."""
    query = query.strip()
    if len(query) < 2:
        return []
    async with session_scope() as session:
        institutions = await ei_crud.search_by_name(session, query)
    return [
        InstitutionCandidate(id_=i.id, name=i.name) for i in institutions
    ]


async def register_student(
    *,
    max_id: int,
    city_id: int,
    institution_id: int,
    fio: str,
    year: int,
    group: str,
    login: str,
    password: str,
) -> None:
    """Регистрирует учащегося.
    """
    fio_parts = fio.strip().split()
    if len(fio_parts) < 2:
        raise RegistrationError(
            "ФИО должно содержать как минимум фамилию и имя."
        )
    surname = fio_parts[0]
    name = fio_parts[1]
    patronymic = " ".join(fio_parts[2:]) if len(fio_parts) > 2 else None

    async with session_scope() as session:
        # Проверка повторной регистрации
        if await student_crud.exists_by_max_id(session, max_id):
            raise RegistrationError("Вы уже зарегистрированы.")

        # Проверка логина
        if await student_crud.exists_by_login(session, login):
            raise RegistrationError("Логин уже занят, выберите другой.")

        # Проверка города
        city = await city_crud.get(session, city_id)
        if city is None:
            raise RegistrationError("Город не найден.")

        # Проверка учреждения и его принадлежности городу
        institution = await ei_crud.get(session, institution_id)
        if institution is None:
            raise RegistrationError("Учреждение не найдено.")
        if institution.city_id != city_id:
            raise RegistrationError(
                "Учреждение не относится к выбранному городу."
            )

        # Создание ученика
        await student_crud.create(
            session,
            name=name,
            surname=surname,
            patronymic=patronymic,
            grade=year,
            student_group=group,
            max_id=max_id,
            login=login,
            password=password,
            EI_id=institution_id,
        )


async def submit_partner_application(
    *,
    max_id: int,
    partner_type: str,
    proposal: str,
    contacts: str,
) -> None:
    """Отправляет заявку партнёра."""
    from db.crud import application as application_crud

    async with session_scope() as session:
        await application_crud.create(
            session,
            max_id=max_id,
            type=partner_type,
            partner_name=proposal[:255],
            description=proposal,
            contact_details=contacts,
        )