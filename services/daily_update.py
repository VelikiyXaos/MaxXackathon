"""Ежедневный опрос ЭСУО и обновление баллов/бонусов в 00:00.

Порядок работы (по ТЗ):
    1. Опрос всех студентов в ЭСУО на обновление оценок → начисление опыта.
    2. Проверка всех существующих бонусов на истечение срока действия.
    3. После обновления баллов — обновление информации о доступных
       студенту бонусах.

Использует функции из веток:
    * EGAS_connector — connection.ABS_grade_provider.AbstractGradeProvider,
      connection.grade_provider_NetSchoolAPI.EgasGradeProvider;
    * bonus — services.bonus.grant_available_bonuses,
      db.crud.bonus / db.crud.student_bonus.

Недостающие функции оформлены прототипами (NotImplementedError)
и описаны в docs/Прототипы недостающих функций.md.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from connection import AbstractGradeProvider
from connection.factory import get_grade_provider
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
    bonuses_granted: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Шаг 1. Опрос ЭСУО и обновление опыта
# ---------------------------------------------------------------------------

async def update_student_experience(
    student_id: int,
    provider: AbstractGradeProvider | None = None,
) -> int:
    """
    Опрашивает ЭСУО об оценках одного студента и пересчитывает опыт.

    Опыт — абсолютное значение за текущий учебный год (см.
    calculate_and_save_school_experience): 1 сентября он обнуляется,
    ежедневный пересчёт идемпотентен.

    Args:
        student_id: ID студента.
        provider: Готовый провайдер оценок. Если None — подбирается
            автоматически через connection.factory.get_grade_provider().

    Returns:
        Изменение опыта (дельту) за этот прогон.
    """
    if provider is None:
        provider = await get_grade_provider(student_id)

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
        except NotImplementedError as exc:
            # Прототип ещё не реализован — не валит весь прогон.
            report.students_failed += 1
            report.errors.append(f"student {student.id}: {exc}")
            logger.warning("Прототип не реализован: %s", exc)
        except Exception as exc:  # noqa: BLE001 — изоляция ошибок по студенту
            report.students_failed += 1
            report.errors.append(f"student {student.id}: {exc}")
            logger.exception("Не удалось обновить оценки студента %s", student.id)


# ---------------------------------------------------------------------------
# Шаг 2. Проверка бонусов на истечение срока действия
# ---------------------------------------------------------------------------

async def expire_bonuses(
    report: DailyUpdateReport,
    *,
    today: date | None = None,
) -> None:
    """
    Проверяет все существующие бонусы на истечение срока действия
    и отзывает просроченные бонусы у всех студентов.

    Args:
        report: Отчёт, куда складываются id истёкших бонусов.
        today: Текущая дата (для тестов).
    """
    current = today or date.today()

    async with session_scope() as session:
        expired = await bonus_crud.get_expired(session, date_now=current)
        for bonus in expired:
            student_ids = await student_bonus_crud.get_student_ids_for_bonus(
                session, bonus.id
            )
            for student_id in student_ids:
                await student_bonus_crud.remove(
                    session, student_id=student_id, bonus_id=bonus.id
                )
            report.expired_bonus_ids.append(bonus.id)
            logger.info("Бонус %s истёк и отозван у %s студентов", bonus.id, len(student_ids))


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
    """Выполняет полный цикл: оценки → сроки бонусов → доступные бонусы."""
    report = DailyUpdateReport()
    logger.info("Ежедневное обновление: старт")

    await update_all_students_grades(report)

    # Шаг 2 может опираться на ещё не реализованный прототип
    # (bonus_crud.get_expired) — не должны из-за него отменяться шаги 1 и 3.
    try:
        await expire_bonuses(report)
    except NotImplementedError as exc:
        report.errors.append(f"expire_bonuses: {exc}")
        logger.warning("Проверка сроков бонусов пропущена: %s", exc)
    except Exception:  # noqa: BLE001 — шаг не должен валить прогон
        report.errors.append("expire_bonuses: unexpected error")
        logger.exception("Ошибка при проверке сроков бонусов")

    await refresh_available_bonuses(report)

    logger.info(
        "Ежедневное обновление: готово (студентов %s, обновлено %s, "
        "ошибок %s, ΔXP %s, истекло бонусов %s, выдано бонусов %s)",
        report.students_total,
        report.students_updated,
        report.students_failed,
        report.xp_awarded,
        len(report.expired_bonus_ids),
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
