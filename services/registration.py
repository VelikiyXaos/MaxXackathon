from dataclasses import dataclass

from db.crud import application as application_crud
from db.crud import city as city_crud
from db.crud import educational_institution as ei_crud
from db.crud import student as student_crud
from db.crud import subject as subject_crud
from db.models import Student

from . import crypto, session_scope

MIN_QUERY_LEN = 2


@dataclass
class SubjectCandidate:
    id_: int
    name: str


@dataclass
class CityCandidate:
    id_: int
    name: str


@dataclass
class InstitutionCandidate:
    id_: int
    name: str


class RegistrationError(Exception):
    pass


async def search_subjects_by_city(query: str) -> list[SubjectCandidate]:
    """Находит регионы, в которых есть город с таким названием"""
    query = query.strip()
    if len(query) < MIN_QUERY_LEN:
        return []

    async with session_scope() as session:
        subjects = await subject_crud.search_by_city_name(session, query)
    return [SubjectCandidate(id_=item.id, name=item.name) for item in subjects]


async def search_cities_in_subject(
    subject_id: int, query: str
) -> list[CityCandidate]:
    """Ищет города внутри выбранного региона по подстроке названия"""
    query = query.strip()
    if len(query) < MIN_QUERY_LEN:
        return []

    async with session_scope() as session:
        cities = await city_crud.search_by_subject_and_name(
            session, subject_id, query
        )
    return [CityCandidate(id_=item.id, name=item.name) for item in cities]


async def search_institutions(query: str) -> list[InstitutionCandidate]:
    """Ищет образовательные учреждения по подстроке названия"""
    query = query.strip()
    if len(query) < MIN_QUERY_LEN:
        return []

    async with session_scope() as session:
        institutions = await ei_crud.search_by_name(session, query)
    return [
        InstitutionCandidate(id_=item.id, name=item.name)
        for item in institutions
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
) -> Student:
    """Регистрирует учащегося и возвращает созданную запись"""
    parts = fio.strip().split()
    if len(parts) < 2:
        raise RegistrationError(
            "ФИО должно содержать как минимум фамилию и имя."
        )

    surname = parts[0]
    name = parts[1]
    patronymic = " ".join(parts[2:]) if len(parts) > 2 else None

    async with session_scope() as session:
        if await student_crud.exists_by_max_id(session, max_id):
            raise RegistrationError("Вы уже зарегистрированы.")

        if await student_crud.exists_by_login(session, login):
            raise RegistrationError("Логин уже занят, выберите другой.")

        city = await city_crud.get(session, city_id)
        if city is None:
            raise RegistrationError("Город не найден.")

        institution = await ei_crud.get(session, institution_id)
        if institution is None:
            raise RegistrationError("Учреждение не найдено.")
        if institution.city_id != city_id:
            raise RegistrationError(
                "Учреждение не относится к выбранному городу."
            )

        return await student_crud.create(
            session,
            name=name,
            surname=surname,
            patronymic=patronymic,
            grade=year,
            student_group=group,
            max_id=max_id,
            login=login,
            password=crypto.encrypt(password),
            EI_id=institution_id,
        )


async def submit_partner_application(
    *,
    max_id: int,
    partner_type: str,
    partner_name: str,
    proposal: str,
    contacts: str,
) -> None:
    """Сохраняет заявку партнёра"""
    async with session_scope() as session:
        await application_crud.create(
            session,
            max_id=max_id,
            type=partner_type,
            partner_name=partner_name,
            description=proposal,
            contact_details=contacts,
        )
