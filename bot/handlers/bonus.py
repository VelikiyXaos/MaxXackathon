from datetime import datetime

from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.helpers import message_text
from bot.keyboards import commercial_partner_menu_keyboard
from bot.states import BonusAdding
from services import auth, bonuses

router = Router(router_id="bonus")

DATE_FORMATS = ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y")


def _parse_date(raw: str) -> datetime | None:
    """Разбирает дату в одном из поддерживаемых форматов"""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


@router.message_created(states=BonusAdding.NAME)
async def on_bonus_name(event: MessageCreated, context):
    """Название бонуса принято: запрашиваем уровень"""
    await context.update_data(bonus_name=message_text(event))
    await context.set_state(BonusAdding.CONDITION)
    await event.message.answer(text=messages.BONUS_CONDITION_REQUEST)


@router.message_created(states=BonusAdding.CONDITION)
async def on_bonus_condition(event: MessageCreated, context):
    """Уровень принят: запрашиваем срок действия"""
    try:
        level = int(message_text(event))
    except ValueError:
        level = 0

    if not bonuses.MIN_BONUS_LEVEL <= level <= bonuses.MAX_BONUS_LEVEL:
        await event.message.answer(text=messages.BONUS_LEVEL_INVALID)
        return

    await context.update_data(bonus_level=level)
    await context.set_state(BonusAdding.DEADLINE)
    await event.message.answer(text=messages.BONUS_DEADLINE_REQUEST)


@router.message_created(states=BonusAdding.DEADLINE)
async def on_bonus_deadline(event: MessageCreated, context):
    """Срок принят: запрашиваем промокод"""
    end_date = _parse_date(message_text(event))

    if end_date is None:
        await event.message.answer(text=messages.BONUS_DEADLINE_INVALID)
        return

    await context.update_data(bonus_deadline=end_date.date())
    await context.set_state(BonusAdding.PROMO)
    await event.message.answer(text=messages.BONUS_PROMO_REQUEST)


@router.message_created(states=BonusAdding.PROMO)
async def on_bonus_promo(event: MessageCreated, context):
    """Промокод принят: сохраняем бонус и возвращаемся в меню"""
    data = await context.get_data()
    promo = message_text(event)
    await context.update_data(bonus_promo=promo)

    partner_max_id = event.get_ids()[1] or 0
    if await auth.get_partner(partner_max_id) is None:
        await context.clear()
        await event.message.answer(text=messages.UNKNOWN_COMMAND)
        return

    deadline = data.get("bonus_deadline")
    if deadline is None:
        await event.message.answer(text=messages.BONUS_DEADLINE_INVALID)
        return

    level = data.get("bonus_level")
    if level is None:
        await event.message.answer(text=messages.BONUS_LEVEL_INVALID)
        return

    try:
        await bonuses.add_bonus(
            partner_max_id=partner_max_id,
            name=data.get("bonus_name", ""),
            level=level,
            deadline=deadline,
            promocode=promo,
        )
    except ValueError as exc:
        await event.message.answer(text=str(exc))
        return

    await context.clear()
    await event.message.answer(
        text=messages.BONUS_ADDED,
        attachments=[commercial_partner_menu_keyboard()],
    )
