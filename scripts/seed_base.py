from __future__ import annotations

import logging

from db.crud import subject as subject_crud
from scripts.regions_ru import EXPECTED_COUNT, SUBJECTS
from services import session_scope

logger = logging.getLogger("seed_base")


async def seed_subjects() -> tuple[int, int]:
    """Добавляет в базу справочник субъектов РФ и отдаёт счётчики"""
    created = 0
    existed = 0

    if len(SUBJECTS) != len(set(SUBJECTS)):
        logger.error("В SUBJECTS есть дубликаты — проверьте scripts/regions_ru.py")
    elif len(SUBJECTS) != EXPECTED_COUNT:
        logger.warning(
            "В справочнике %d субъектов, ожидалось %d — сверьтесь "
            "со scripts/regions_ru.py",
            len(SUBJECTS),
            EXPECTED_COUNT,
        )

    async with session_scope() as session:
        for name in SUBJECTS:
            if await subject_crud.get_by_name(session, name) is not None:
                existed += 1
                continue
            await subject_crud.create(session, name=name)
            created += 1
            logger.info("Добавлен субъект РФ: %s", name)

    logger.info(
        "Субъекты РФ готовы: создано %d, уже было %d, всего в справочнике %d",
        created,
        existed,
        len(SUBJECTS),
    )
    return created, existed


async def main() -> int:
    """Настраивает логи и наполняет базу справочником субъектов РФ"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s"
    )
    await seed_subjects()
    return 0
