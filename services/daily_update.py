from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from connection import AbstractEgasConnector
from connection.factory import get_egas_connector
from db.crud import bonus as bonus_crud
from db.crud import student as student_crud
from db.crud import student_bonus as student_bonus_crud
from services import session_scope
from services.bonus import grant_available_bonuses
from services.experience import calculate_and_save_school_experience

logger = logging.getLogger(__name__)

@dataclass
class DailyUpdateReport:
    """Итог одного ночного прогона"""

    students_total: int = 0
    students_updated: int = 0
    students_failed: int = 0
    xp_awarded: int = 0
    expired_bonus_ids: list[int] = field(default_factory=list)
    bonus_links_revoked: int = 0
    bonuses_granted: int = 0
    errors: list[str] = field(default_factory=list)

async def update_student_experience(
    student_id: int,
    provider: AbstractEgasConnector | None = None,
) -> int:
    """Опрашивает ЭСУО об оценках одного студента и пересчитывает опыт"""
    if provider is None:
        provider = await get_egas_connector(student_id)

    async with provider:
        grades = await provider.get_grades_count(student_id=student_id)

    return await calculate_and_save_school_experience(student_id, grades)


async def update_all_students_grades(report: DailyUpdateReport) -> None:
    """Опрашивает ЭСУО по всем студентам и пересчитывает их опыт"""
    async with session_scope() as session:
        students = await student_crud.get_all(session)

    report.students_total = len(students)

    for student in students:
        try:
            xp = await update_student_experience(student.id)
            report.students_updated += 1
            report.xp_awarded += xp
        except Exception as exc:
            report.students_failed += 1
            report.errors.append(f"student {student.id}: {exc}")
            logger.exception("Не удалось обновить оценки студента %s", student.id)

async def expire_bonuses(
    report: DailyUpdateReport,
    *,
    today: date | None = None,
) -> None:
    """Проверяет все существующие бонусы на истечение срока действия"""
    current = today or date.today()

    async with session_scope() as session:
        expired = await bonus_crud.get_expired(session, date_now=current)
        for bonus in expired:
            bonus_id = bonus.id
            links = await student_bonus_crud.count_students_for_bonus(
                session, bonus_id
            )
            await bonus_crud.delete(session, bonus_id)
            report.expired_bonus_ids.append(bonus_id)
            report.bonus_links_revoked += links
            logger.info(
                "Бонус %s истёк: удалён вместе с %s выдачами студентам",
                bonus_id,
                links,
            )

async def refresh_available_bonuses(report: DailyUpdateReport) -> None:
    """Обновляет информацию о бонусах, доступных каждому студенту"""
    async with session_scope() as session:
        students = await student_crud.get_all(session)

    for student in students:
        try:
            granted = await grant_available_bonuses(student.id)
            report.bonuses_granted += len(granted)
            if granted:
                logger.info(
                    "Студент %s получил доступных бонусов: %s",
                    student.id,
                    len(granted),
                )
        except Exception as exc:
            report.errors.append(f"bonuses for student {student.id}: {exc}")
            logger.exception(
                "Не удалось обновить бонусы студента %s", student.id
            )

async def run_daily_update() -> DailyUpdateReport:
    """Выполняет полный цикл обновления: сроки бонусов → оценки/опыт → доступные бонусы"""
    report = DailyUpdateReport()
    logger.info("Ежедневное обновление: старт")

    try:
        await expire_bonuses(report)
    except Exception:
        report.errors.append("expire_bonuses: unexpected error")
        logger.exception("Ошибка при удалении истёкших бонусов")

    await update_all_students_grades(report)

    await refresh_available_bonuses(report)

    logger.info(
        "Ежедневное обновление: готово (студентов %s, обновлено %s, "
        "ошибок %s, ΔXP %s, истекло бонусов %s, отозвано связей %s, "
        "выдано бонусов %s)",
        report.students_total,
        report.students_updated,
        report.students_failed,
        report.xp_awarded,
        len(report.expired_bonus_ids),
        report.bonus_links_revoked,
        report.bonuses_granted,
    )
    return report

def seconds_until(target: time, now: datetime | None = None) -> float:
    """Сколько секунд до ближайшего наступления времени `target`"""
    current = now or datetime.now()
    next_run = datetime.combine(current.date(), target)
    if next_run <= current:
        next_run += timedelta(days=1)
    return (next_run - current).total_seconds()


async def daily_update_loop(run_at: time = time(0, 0)) -> None:
    """Бесконечный цикл: запускает run_daily_update() каждый день в `run_at`"""
    while True:
        delay = seconds_until(run_at)
        logger.info(
            "Следующее ежедневное обновление: через %.0f c (%s)",
            delay,
            (datetime.now() + timedelta(seconds=delay)).isoformat(sep=" ", timespec="seconds"),
        )
        await asyncio.sleep(delay)
        try:
            await run_daily_update()
        except Exception:
            logger.exception("Ежедневное обновление завершилось с ошибкой")
