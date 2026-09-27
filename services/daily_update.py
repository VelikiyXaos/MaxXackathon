"""Ежедневный опрос ЭСУО и обновление баллов/бонусов в 00:00.

Порядок работы (по ТЗ):
    1. Проверка всех существующих бонусов на истечение срока действия:
       истёкшие удаляются из таблицы бонусов и из связи со студентами
       (каскадом на уровне БД).
    2. Опрос всех студентов в ЭСУО на обновление оценок → начисление опыта.
    3. После обновления баллов — обновление информации о доступных
       студенту бонусах.

Использует функции из веток:
    * EGAS_connector — connection.ABS_egas_connector.AbstractEgasConnector,
      connection.registry (реестр коннекторов), connection.factory;
    * bonus — services.bonus.grant_available_bonuses,
      db.crud.bonus / db.crud.student_bonus.
"""

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


# ---------------------------------------------------------------------------
# Отчёт о прогоне
# ---------------------------------------------------------------------------

@dataclass
class DailyUpdateReport:
    """Итог одного ночного прогона."""

    students_total: int = 0
    students_updated: int = 0
    students_failed: int = 0
    xp_awarded: int = 0  # суммарная ДЕЛЬТА опыта (новое − предыдущее)
    expired_bonus_ids: list[int] = field(default_factory=list)
    bonus_links_revoked: int = 0
    bonuses_granted: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Шаг 2. Опрос ЭСУО и обновление опыта
# ---------------------------------------------------------------------------

async def update_student_experience(
    student_id: int,
    provider: AbstractEgasConnector | None = None,
) -> int:
    """
    Опрашивает ЭСУО об оценках одного студента и пересчитывает опыт.

    Опыт — абсолютное значение за текущий учебный год (см.
    calculate_and_save_school_experience): 1 сентября он обнуляется,
    ежедневный пересчёт идемпотентен.

    Args:
        student_id: ID студента.
        provider: Готовый коннектор ЭСУО. Если None — подбирается
            автоматически через connection.factory.get_egas_connector().

    Returns:
        Изменение опыта (дельту) за этот прогон.
    """
    if provider is None:
        provider = await get_egas_connector(student_id)

    async with provider:
        grades = await provider.get_grades_count(student_id=student_id)

    return await calculate_and_save_school_experience(student_id, grades)


async def update_all_students_grades(report: DailyUpdateReport) -> None:
    """Опрашивает ЭСУО по всем студентам и пересчитывает их опыт."""
    async with session_scope() as session:
        students = await student_crud.get_all(session)

    report.students_total = len(students)

    for student in students:
        try:
            xp = await update_student_experience(student.id)
            report.students_updated += 1
            report.xp_awarded += xp
        except Exception as exc:  # noqa: BLE001 — изоляция ошибок по студенту
            report.students_failed += 1
            report.errors.append(f"student {student.id}: {exc}")
            logger.exception("Не удалось обновить оценки студента %s", student.id)


# ---------------------------------------------------------------------------
# Шаг 1. Проверка бонусов на истечение срока действия
# ---------------------------------------------------------------------------

async def expire_bonuses(
    report: DailyUpdateReport,
    *,
    today: date | None = None,
) -> None:
    """
    Проверяет все существующие бонусы на истечение срока действия:
    истёкший бонус удаляется из БД вместе со всеми выдачами студентам.

    Связи `student_bonus` удаляет сама база: у внешнего ключа
    `student_bonus.bonus_id → bonus.id` стоит ON DELETE CASCADE
    (см. db/models/associations.py и миграцию
    alembic/versions/3a7c1d5e9b42_student_bonus_bonus_cascade.py),
    поэтому достаточно удалить сам бонус. Размер каскада считаем
    заранее — одним запросом на бонус.

    Args:
        report: Отчёт, куда складываются id истёкших бонусов.
        today: Текущая дата (для тестов).
    """
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


# ---------------------------------------------------------------------------
# Шаг 3. Обновление доступных студентам бонусов
# ---------------------------------------------------------------------------

async def refresh_available_bonuses(report: DailyUpdateReport) -> None:
    """Обновляет информацию о бонусах, доступных каждому студенту."""
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
        except Exception as exc:  # noqa: BLE001 — изоляция ошибок по студенту
            report.errors.append(f"bonuses for student {student.id}: {exc}")
            logger.exception(
                "Не удалось обновить бонусы студента %s", student.id
            )


# ---------------------------------------------------------------------------
# Полный ночной прогон
# ---------------------------------------------------------------------------

async def run_daily_update() -> DailyUpdateReport:
    """Выполняет полный цикл: сроки бонусов → оценки/опыт → доступные бонусы."""
    report = DailyUpdateReport()
    logger.info("Ежедневное обновление: старт")

    # Шаг 1: истёкшие бонусы удаляются до пересчёта опыта и выдачи новых,
    # чтобы они не попали в выдачу этого же прогона.
    try:
        await expire_bonuses(report)
    except Exception:  # noqa: BLE001 — шаг не должен валить прогон
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


# ---------------------------------------------------------------------------
# Планировщик: ежедневно в 00:00
# ---------------------------------------------------------------------------

def seconds_until(target: time, now: datetime | None = None) -> float:
    """Сколько секунд до ближайшего наступления времени `target`."""
    current = now or datetime.now()
    next_run = datetime.combine(current.date(), target)
    if next_run <= current:
        next_run += timedelta(days=1)
    return (next_run - current).total_seconds()


async def daily_update_loop(run_at: time = time(0, 0)) -> None:
    """
    Бесконечный цикл: запускает run_daily_update() каждый день в run_at.

    Запускается задачей из bot.main.main().
    """
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
        except Exception:  # noqa: BLE001 — цикл не должен умирать
            logger.exception("Ежедневное обновление завершилось с ошибкой")
