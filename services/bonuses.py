# services

from datetime import date, datetime

from db.crud import bonus as bonus_crud
from db.crud import partner as partner_crud
from db.crud import student as student_crud
from db.crud import student_bonus as student_bonus_crud
from . import session_scope

def _serialize_bonus(bonus) -> dict:
    return {
        "id": bonus.id,
        "promocode": bonus.promocode,
        "need_experience": bonus.need_experience,
        "partner_id": bonus.partner_id,
        "end_date": bonus.end_date.isoformat() if bonus.end_date else None,
    }


async def get_student_bonuses(max_id: int) -> list[dict]:
    """Возвращает список бонусов, выданных учащемуся."""
    async with session_scope() as session:
        student = await student_crud.get_by_max_id(session, max_id)
        if student is None:
            return []

        bonus_ids = await student_bonus_crud.get_bonus_ids_for_student(
            session, student.id
        )
        if not bonus_ids:
            return []

        bonuses = []
        for bonus_id in bonus_ids:
            bonus = await bonus_crud.get(session, bonus_id)
            if bonus is not None:
                bonuses.append(_serialize_bonus(bonus))
        return bonuses



async def get_partner_bonuses(max_id: int) -> list[dict]:
    """Возвращает список бонусов, созданных партнёром."""
    async with session_scope() as session:
        partner = await partner_crud.get_by_max_id(session, max_id)
        if partner is None:
            return []

        bonuses = await bonus_crud.get_by_partner(session, partner.id)
        return [_serialize_bonus(b) for b in bonuses]



async def add_bonus(
    *,
    partner_id: int,
    # name: str,
    condition: str,
    deadline: str,
    promocode: str,
) -> None:
    """Добавляет новый бонус от партнёра."""
    need_experience = _parse_condition(condition)
    end_date = _parse_deadline(deadline)

    if not promocode or not promocode.strip():
        raise ValueError("Промокод не может быть пустым.")

    async with session_scope() as session:
        partner = await partner_crud.get_by_max_id(session, partner_id)
        if partner is None:
            raise ValueError(
                f"Партнёр с max_id={partner_id} не найден."
            )

        await bonus_crud.create(
            session,
            promocode=promocode.strip(),
            need_experience=need_experience,
            partner_id=partner.id,
            end_date=end_date,
        )

# --- 

def _parse_deadline(deadline: str) -> date | None:
    """Парсит дату дедлайна из строки.
    DD.MM.YYYY
    Пустая строка/None = None.
    """
    if not deadline:
        return None
    deadline = deadline.strip()
    if not deadline:
        return None
    for fmt in ("%d.%m.%Y"):
        try:
            return datetime.strptime(deadline, fmt).date()
        except ValueError:
            continue
    raise ValueError(
        f"Не удалось распознать дату. "
        "Требуется формат: DD.MM.YYYY"
    )

def _parse_condition(condition: str) -> int:
    """Извлекает требуемый опыт из строки условия."""
    condition = (condition or "").strip()
    if not condition:
        raise ValueError("Условие бонуса не может быть пустым.")
    digits = ""
    for ch in condition:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    if not digits:
        raise ValueError(
            f"Не удалось извлечь число из условия '{condition}'."
        )
    return int(digits)