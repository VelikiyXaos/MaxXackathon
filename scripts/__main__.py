from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from db.crud import admin as admin_crud
from db.crud import bonus as bonus_crud
from db.crud import egas as egas_crud
from db.crud import subject as subject_crud
from scripts.seed_admin import ADMIN_MAX_ID_ENV, seed_admin, admin_max_id
from scripts.seed_base import seed_subjects
from scripts.seed_test_data import main as seed_test_data
from services import session_scope

logger = logging.getLogger("scripts")


async def _status() -> int:
    async with session_scope() as session:
        subjects = await subject_crud.get_all(session)
        admins = await admin_crud.get_all(session)
        bonuses = await bonus_crud.get_all(session)
        egas_rows = await egas_crud.get_all(session)

        print(f"субъектов РФ:   {len(subjects)}")
        print(f"бонусов:        {len(bonuses)}")
        print(f"ЭСУО:           {len(egas_rows)}")
        for row in egas_rows:
            print(f"  - {row.name} ({row.API_file})")
        print(f"администраторов: {len(admins)}")
        for row in admins:
            print(f"  - max_id={row.max_id}")

    configured = admin_max_id()
    if configured is None:
        if not admins:
            print(
                f"\n{ADMIN_MAX_ID_ENV} не задан укажите его в .env и запустите `python -m scripts seed-admin`"
            )
    return 0


async def _init(*, with_test: bool, required_admin: bool) -> int:
    await seed_subjects()
    if with_test:
        await seed_test_data()
    code = await seed_admin(required=required_admin)
    logger.info("Инициализация завершена")
    return code


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m scripts",
        description="Запуск и первичное заполнение базы данных.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("init", help="основные + тестовые данные + админ")
    run.add_argument(
        "--no-test",
        action="store_true",
        help="не создавать тестовые данные",
    )
    run.add_argument(
        "--required-admin",
        action="store_true",
        help="считать отсутствие %s ошибкой" % ADMIN_MAX_ID_ENV,
    )

    sub.add_parser("seed-base", help="справочник субъектов РФ")

    sub.add_parser("seed-test", help="тестовые данные")

    admin = sub.add_parser("seed-admin", help="первый администратор из .env")
    admin.add_argument(
        "--required", action="store_true", help="считать отсутствие max_id ошибкой"
    )

    sub.add_parser("status", help="сводка по базе")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    async def run() -> int:
        if args.command == "init":
            return await _init(
                with_test=not args.no_test,
                required_admin=args.required_admin,
            )
        if args.command == "seed-base":
            await seed_subjects()
            return 0
        if args.command == "seed-test":
            return await seed_test_data()
        if args.command == "seed-admin":
            return await seed_admin(required=args.required)
        if args.command == "status":
            return await _status()
        return 1

    return asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())
