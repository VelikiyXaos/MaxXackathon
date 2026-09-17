from dataclasses import dataclass


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


async def search_cities(query: str) -> list[CityCandidate]:
    # TODO: реализовать поиск городов/регионов по названию
    return []


async def search_institutions(query: str) -> list[InstitutionCandidate]:
    # TODO: реализовать поиск образовательных учреждений
    return []


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
    # TODO: реализовать регистрацию учащегося
    # (db.crud.student.create + проверка по ЭГАС/ОУ).
    return None


async def submit_partner_application(
    *,
    max_id: int,
    partner_type: str,
    proposal: str,
    contacts: str,
) -> None:
    # TODO: реализовать отправку заявки партнёра
    return None