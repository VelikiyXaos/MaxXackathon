from __future__ import annotations

import logging
import os

from db.crud import admin as admin_crud
from services import session_scope

logger = logging.getLogger("seed_admin")

ADMIN_MAX_ID_ENV = "ADMIN_MAX_ID"

INT32_MAX = 2_147_483_647


def admin_max_id() -> int | None:
    raw = os.getenv(ADMIN_MAX_ID_ENV, "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        logger.warning("%s=%r не число — админ не создан", ADMIN_MAX_ID_ENV, raw)
        return None
    if value <= 0 or value > INT32_MAX:
        logger.warning(
            "%s=%d вне диапазона Integer — админ не создан", ADMIN_MAX_ID_ENV, value
        )
        return None
    return value


async def seed_admin(*, required: bool = False) -> int:
    max_id = admin_max_id()

    if max_id is None:
        message = (
            "%s не задан — администратор не создан. Укажите max_id "
            "администратора в .env и запустите скрипт ещё раз."
        ) % ADMIN_MAX_ID_ENV
        if required:
            logger.error("%s", message)
            return 1
        logger.warning("%s", message)
        return 0

    async with session_scope() as session:
        existing = await admin_crud.get_by_max_id(session, max_id)
        if existing is not None:
            logger.info(
                "Администратор уже есть: max_id=%d (id=%d)", max_id, existing.id
            )
            return 0

        admin = await admin_crud.create(session, max_id=max_id)
        logger.info("Создан первый администратор: max_id=%d (id=%d)", max_id, admin.id)

    return 0
