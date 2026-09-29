# services

from datetime import date

from db.crud import bonus as bonus_crud
from db.crud import partner as partner_crud
from db.crud import student as student_crud
from db.crud import student_bonus as student_bonus_crud
from . import session_scope
from .experience import get_level_for_xp, get_xp_for_level

MIN_BONUS_LEVEL = 1
MAX_BONUS_LEVEL = 15

# Ширина колонки bonus.name в БД: длинное имя молча уронило бы
# коммит DataError'ом, минуя ValueError, который ловит хендлер.
MAX_BONUS_NAME_LEN = 255

def _serialize_bonus(bonus) -> dict:
    return {
        "id": bonus.id,
        "name": bonus.name,
        "promocode": bonus.promocode,
        "need_experience": bonus.need_experience,
        "level": get_level_for_xp(bonus.need_experience),
        "partner_id": bonus.partner_id,
        "end_date": bonus.end_date.isoformat() if bonus.end_date else None,
    }


async def get_student_bonuses(student_max_id: int) -> list[dict]:
    """Возвращает список бонусов, выданных учащемуся."""
    async with session_scope() as session:
        student = await student_crud.get_by_max_id(session, student_max_id)
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



async def get_partner_bonuses(partner_max_id: int) -> list[dict]:
    """Возвращает список бонусов, созданных партнёром."""
    async with session_scope() as session:
        partner = await partner_crud.get_by_max_id(session, partner_max_id)
        if partner is None:
            return []

        bonuses = await bonus_crud.get_by_partner(session, partner.id)
        return [_serialize_bonus(b) for b in bonuses]



async def get_available_bonuses(student_max_id: int) -> list[dict]:
    """Возвращает бонусы, доступные ученику по опыту и сроку действия.

    Уже полученные бонусы из списка убираются: порог и срок
    фильтрует сам bonus_crud.get_available, а факт получения
    известен только через связь student_bonus.
    """
    async with session_scope() as session:
        student = await student_crud.get_by_max_id(session, student_max_id)
        if student is None:
            return []

        taken = set(
            await student_bonus_crud.get_bonus_ids_for_student(
                session, student.id
            )
        )
        available = await bonus_crud.get_available(session, student.experience)
        return [_serialize_bonus(b) for b in available if b.id not in taken]


async def issue_bonus(student_max_id: int, bonus_id: int) -> dict:
    """Выдаёт бонус ученику и возвращает его для показа промокода.

    Все проверки продублированы в сервисе, а не только в хендлере:
    кнопка в истории сообщений может устареть, и условия должны
    быть перепроверены на сервере в момент выдачи.

    Raises:
        ValueError: с текстом для пользователя, если ученик или бонус
            не найден, не хватает опыта, срок истёк или бонус уже получен.
    """
    async with session_scope() as session:
        student = await student_crud.get_by_max_id(session, student_max_id)
        if student is None:
            raise ValueError("Ученик не найден.")

        bonus = await bonus_crud.get(session, bonus_id)
        if bonus is None:
            raise ValueError("Бонус не найден.")

        if bonus.need_experience > student.experience:
            raise ValueError(
                "Этот бонус пока недоступен: не хватает опыта."
            )

        if bonus.end_date is not None and bonus.end_date < date.today():
            raise ValueError("Срок действия этого бонуса истёк.")

        if await student_bonus_crud.exists(
            session, student_id=student.id, bonus_id=bonus_id
        ):
            raise ValueError("Этот бонус уже получен.")

        await student_bonus_crud.add(
            session, student_id=student.id, bonus_id=bonus_id
        )

    return _serialize_bonus(bonus)


async def add_bonus(
    *,
    partner_max_id: int,
    name: str | None = None,
    level: int,
    deadline: date | None,
    promocode: str,
) -> None:
    """Добавляет новый бонус от партнёра.

    Партнёр задаёт уровень, а в БД хранится порог опыта этого
    уровня: need_experience = get_xp_for_level(level).
    deadline — уже распарсенная вызывающим кодом дата (или None).
    name необязателен: пустое заменяется на «Бонус от <компания>».
    """
    if not MIN_BONUS_LEVEL <= level <= MAX_BONUS_LEVEL:
        raise ValueError(
            f"Уровень должен быть от {MIN_BONUS_LEVEL} "
            f"до {MAX_BONUS_LEVEL}, получено {level}."
        )

    need_experience = get_xp_for_level(level)

    if not promocode or not promocode.strip():
        raise ValueError("Промокод не может быть пустым.")

    async with session_scope() as session:
        partner = await partner_crud.get_by_max_id(session, partner_max_id)
        if partner is None:
            raise ValueError(
                f"Партнёр с max_id={partner_max_id} не найден."
            )

        # Заглушка собирается после загрузки партнёра, потому что
        # нужна его компания.
        bonus_name = (name or "").strip()
        if not bonus_name:
            # Свой текст обрезаем по лимиту колонки, а не ругаемся:
            # partner.name бывает длиной 255, и «Бонус от » сверху
            # вытолкнул бы партнёра за лимит своим же названием.
            bonus_name = f"Бонус от {partner.name}"[:MAX_BONUS_NAME_LEN]
        elif len(bonus_name) > MAX_BONUS_NAME_LEN:
            raise ValueError(
                f"Название бонуса длиннее {MAX_BONUS_NAME_LEN} символов."
            )

        await bonus_crud.create(
            session,
            name=bonus_name,
            promocode=promocode.strip(),
            need_experience=need_experience,
            partner_id=partner.id,
            end_date=deadline,
        )
