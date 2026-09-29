from __future__ import annotations

import logging
import os

from connection.connectors.mock_demo import MockEgasConnector
from db.crud import bonus as bonus_crud
from db.crud import city as city_crud
from db.crud import educational_institution as ei_crud
from db.crud import egas as egas_crud
from db.crud import ei_with_egas as ei_with_egas_crud
from db.crud import partner as partner_crud
from db.crud import subject as subject_crud
from services import session_scope
from services.experience import get_xp_for_level

logger = logging.getLogger("seed_test")

TEST_SUBJECT = "Волгоградская область"
TEST_CITY = "Волгоград"

MAX_LEVEL = 15

DEFAULT_TEST_PARTNER_MAX_ID = 1_000_000_001

INT32_MIN = -2_147_483_648
INT32_MAX = 2_147_483_647


def _int_env(name: str, default: int) -> int:
    """Читает целое из окружения, проверяя попадание в Integer (int32)"""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("%s=%r не число — беру %d", name, raw, default)
        return default
    if not INT32_MIN <= value <= INT32_MAX:
        logger.warning(
            "%s=%d вне диапазона Integer — беру %d", name, value, default
        )
        return default
    return value


async def _ensure_subject_and_city() -> tuple[int, int]:
    """Создаёт тестовые субъект РФ и город, отдавая их id"""
    async with session_scope() as session:
        subject = await subject_crud.get_by_name(session, TEST_SUBJECT)
        if subject is None:
            subject = await subject_crud.create(session, name=TEST_SUBJECT)
            logger.info("Создан субъект РФ для теста: %s", TEST_SUBJECT)

        city = await city_crud.get_by_name(session, TEST_CITY, subject.id)
        if city is None:
            city = await city_crud.create(
                session, name=TEST_CITY, subject_id=subject.id
            )
            logger.info("Создан город для теста: %s", city.name)

    return subject.id, city.id


async def _ensure_school(city_id: int) -> int:
    """Создаёт тестовую школу в городе и отдаёт её id"""
    name = "Школа №1"
    async with session_scope() as session:
        school = await ei_crud.get_by_name(session, name)
        if school is None:
            school = await ei_crud.create(session, name=name, city_id=city_id)
            logger.info("Создана тестовая школа: %s (id=%d)", school.name, school.id)
        elif school.city_id != city_id:
            logger.info(
                "У школы «%s» другой город (city_id=%d, ожидался %d) — переношу",
                name,
                school.city_id,
                city_id,
            )
            school = await ei_crud.update(session, school.id, city_id=city_id)
        return school.id


async def _ensure_partner() -> int:
    """Создаёт тестового партнёра и отдаёт его id"""
    name = "Партнёр"
    max_id = _int_env("TEST_PARTNER_MAX_ID", DEFAULT_TEST_PARTNER_MAX_ID)
    async with session_scope() as session:
        partner = await partner_crud.get_by_name(session, name)
        if partner is None:
            partner = await partner_crud.create(
                session, name=name, max_id=max_id
            )
            logger.info(
                "Создан тестовый партнёр: %s (max_id=%d, id=%d)",
                partner.name,
                partner.max_id,
                partner.id,
            )
        elif partner.max_id != max_id:
            logger.warning(
                "У партнёра «%s» max_id=%d, а в TEST_PARTNER_MAX_ID=%d — "
                "обновляю",
                name,
                partner.max_id,
                max_id,
            )
            partner = await partner_crud.update(session, partner.id, max_id=max_id)
        return partner.id


async def _ensure_bonuses(partner_id: int) -> int:
    """Создаёт бонусы на каждый уровень и отдаёт число созданных"""
    created = 0
    async with session_scope() as session:
        for level in range(1, MAX_LEVEL + 1):
            need = get_xp_for_level(level)
            promocode = f"TEST-LVL{level:02d}"
            if await bonus_crud.get_by_promocode(session, promocode) is not None:
                continue
            await bonus_crud.create(
                session,
                name=f"Бонус за {level} уровень",
                promocode=promocode,
                need_experience=need,
                partner_id=partner_id,
            )
            created += 1
            logger.info(
                "Бонус %s: уровень %d, порог опыта %d XP", promocode, level, need
            )
    return created


async def _ensure_mock_egas(school_id: int) -> int:
    """Создаёт тестовую ЭСУО-имитацию, подключая её к школе"""
    name = "ЭСУО-имитация (mock_egas)"
    async with session_scope() as session:
        egas = await egas_crud.get_by_name(session, name)
        if egas is None:
            egas = await egas_crud.create(
                session, name=name, API_file=MockEgasConnector.__name__
            )
            logger.info(
                "Создана тестовая ЭСУО: %s (%s, id=%d)",
                egas.name,
                egas.API_file,
                egas.id,
            )
        elif egas.API_file != MockEgasConnector.__name__:
            egas = await egas_crud.update(
                session, egas.id, API_file=MockEgasConnector.__name__
            )
            logger.info("ЭСУО «%s» переключена на %s", name, MockEgasConnector.__name__)

        if not await ei_with_egas_crud.exists(
            session, EI_id=school_id, EGAS_id=egas.id
        ):
            await ei_with_egas_crud.add(
                session, EI_id=school_id, EGAS_id=egas.id
            )
            logger.info("ЭСУО подключена к школе id=%d", school_id)
        return egas.id


async def main() -> int:
    """Настраивает логи и наполняет базу тестовыми данными"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s"
    )

    _, city_id = await _ensure_subject_and_city()
    school_id = await _ensure_school(city_id)
    partner_id = await _ensure_partner()
    bonuses = await _ensure_bonuses(partner_id)
    await _ensure_mock_egas(school_id)

    logger.info(
        "Тестовые данные готовы: школа=%d, партнёр=%d, бонусов +%d",
        school_id,
        partner_id,
        bonuses,
    )
    return 0
