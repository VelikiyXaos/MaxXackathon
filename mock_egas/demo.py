from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, timedelta

from connection.connectors.mock_demo import (
    MockEgasConnector,
    daily_load,
    marks_for_day,
    scenario_for_day,
    set_run_start,
)
from db.crud import educational_institution as ei_crud
from db.crud import egas as egas_crud
from db.crud import ei_with_egas as ei_with_egas_crud
from db.crud import student as student_crud
from services import session_scope
from services.daily_update import run_daily_update
from services.experience import get_student_level_info

MOCK_CLASS = "MockEgasConnector"
REAL_CLASS = "NetSchoolConnector"
MOCK_EGAS_NAME = "ЭСУО-имитация (mock_egas)"
SIMULATED_WEEKS = 4
SIMULATED_DAYS = SIMULATED_WEEKS * 7


async def show_status() -> None:
    """Печатает ЭГАС и подключённые к ним коннекторы"""
    async with session_scope() as session:
        rows = await egas_crud.get_all(session)
        if not rows:
            print("В таблице EGAS нет ни одной ЭГАС.")
            print("Подключить тестовую: python -m mock_egas demo on")
            return
        print(f"{'id':<5}{'name':<34}{'API_file':<24}учреждения")
        for row in rows:
            ei_ids = await ei_with_egas_crud.get_institution_ids_for_egas(
                session, row.id
            )
            print(f"{row.id:<5}{row.name:<34}{row.API_file:<24}{ei_ids or '—'}")


async def switch(target: str) -> None:
    """Переключает все ЭГАС на коннектор target, создавая ЭГАС при нужде"""
    async with session_scope() as session:
        rows = await egas_crud.get_all(session)
        if not rows:
            row = await egas_crud.create(
                session, name=MOCK_EGAS_NAME, API_file=target
            )
            institutions = await ei_crud.get_all(session)
            for institution in institutions:
                await ei_with_egas_crud.add(
                    session, EI_id=institution.id, EGAS_id=row.id
                )
            print(
                f"Создана ЭГАС #{row.id} «{row.name}» ({target}) "
                f"и подключена к учреждениям {[i.id for i in institutions]}"
            )
            return

        for row in rows:
            await egas_crud.update(session, row.id, API_file=target)
            print(f"ЭГАС #{row.id} «{row.name}»: API_file = {target}")


async def run_nights(days: int, start: date) -> None:
    """Прогоняет ночные обновления подряд, начиная с даты start"""
    students_info: list[tuple[int, str]] = []
    async with session_scope() as session:
        for student in await student_crud.get_all(session):
            students_info.append((student.id, f"{student.surname} {student.name}"))

    print(f"Симуляция {days} ночей начиная с {start.isoformat()}\n")
    header = (
        f"{'ночь':<6}{'дата':<12}{'день':<10}{'сценарий':<26}"
        f"{'нагрузка':<10}{'новых':<7}{'ΔXP':<7}итог"
    )
    print(header)
    print("-" * len(header))

    set_run_start(start)
    for index in range(days):
        night = start + timedelta(days=index)
        MockEgasConnector.set_today(night)
        report = await run_daily_update()

        fresh = marks_for_day(night)
        levels = []
        for student_id, name in students_info:
            info = await get_student_level_info(student_id)
            levels.append(
                f"{name}: ур. {info['current_level']} "
                f"({info['progress_percent']}%)"
            )

        print(
            f"{index + 1:<6}{night.isoformat():<12}"
            f"{night.strftime('%a'):<10}{scenario_for_day(night):<26}"
            f"×{daily_load(night):<9}{len(fresh):<7}{report.xp_awarded:<7}"
            f"{'; '.join(levels)}"
        )

    MockEgasConnector.set_today(None)
    set_run_start(None)
    print("\nГотово, «сегодня» снова реальное.")


async def amain(argv: list[str] | None = None) -> int:
    """Разбирает аргументы и выполняет команду, отдавая код возврата"""
    args = _parse(argv)
    try:
        if args.command == "status":
            await show_status()
        elif args.command == "on":
            await switch(MOCK_CLASS)
        elif args.command == "off":
            await switch(REAL_CLASS)
        elif args.command == "nights":
            start = date.fromisoformat(args.start) if args.start else date.today()
            await run_nights(args.days, start)
        return 0
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Разбирает командную строку demo в Namespace"""
    parser = argparse.ArgumentParser(
        prog="python -m mock_egas demo",
        description="Подключение бота к тестовым данным ЭСУО (mock_egas).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="показать ЭГАС и подключённые коннекторы")
    sub.add_parser("on", help="переключить ЭГАС на MockEgasConnector")
    sub.add_parser("off", help="вернуть NetSchoolConnector")
    nights = sub.add_parser("nights", help="прогнать ночи без ожидания 00:00")
    nights.add_argument(
        "--days", type=int, default=SIMULATED_DAYS,
        help=f"сколько ночей (по умолчанию {SIMULATED_WEEKS} недели)",
    )
    nights.add_argument("--start", help="дата первой ночи, ГГГГ-ММ-ДД")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Запускает demo в отдельном цикле событий"""
    return asyncio.run(amain(argv))


if __name__ == "__main__":
    raise SystemExit(main())
