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
    name: str,
    condition: str,
    deadline: str,
    promocode: str,
) -> None:
    # TODO: реализовать добавление бонуса
    return None

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