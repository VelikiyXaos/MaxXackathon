from datetime import datetime

from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.keyboards import commercial_partner_menu_keyboard
from bot.states import BonusAdding
from services import auth, bonuses

router = Router(router_id="bonus")


def _message_text(event: MessageCreated) -> str:
    """Возвращает текст входящего сообщения (или пустую строку)."""
    body = event.message.body
    return body.text.strip() if body and body.text else ""


@router.message_created(states=BonusAdding.NAME)
async def on_bonus_name(event: MessageCreated, context):
    """Название бонуса принято — запрашиваем условие."""
    await context.update_data(bonus_name=_message_text(event))
    await context.set_state(BonusAdding.CONDITION)
    await event.message.answer(text=messages.BONUS_CONDITION_REQUEST)


@router.message_created(states=BonusAdding.CONDITION)
async def on_bonus_condition(event: MessageCreated, context):
    """Условие принято — запрашиваем срок действия."""
    await context.update_data(bonus_condition=_message_text(event))
    await context.set_state(BonusAdding.DEADLINE)
    await event.message.answer(text=messages.BONUS_DEADLINE_REQUEST)


@router.message_created(states=BonusAdding.DEADLINE)
async def on_bonus_deadline(event: MessageCreated, context):
    """Срок принят — запрашиваем промокод."""
    raw = _message_text(event)
    end_date = None
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            end_date = datetime.strptime(raw, fmt).date()
            break
        except ValueError:
            continue

    if end_date is None:
        await event.message.answer(text=messages.BONUS_DEADLINE_INVALID)
        return

    await context.update_data(bonus_deadline=end_date)
    await context.set_state(BonusAdding.PROMO)
    await event.message.answer(text=messages.BONUS_PROMO_REQUEST)


@router.message_created(states=BonusAdding.PROMO)
async def on_bonus_promo(event: MessageCreated, context):
    """Промокод принят — сохраняем бонус и возвращаемся в меню."""
    data = await context.get_data()
    promo = _message_text(event)
    await context.update_data(bonus_promo=promo)

    partner = await auth.get_partner(event.get_ids()[1] or 0)
    if partner is None:
        await context.clear()
        await event.message.answer(text=messages.UNKNOWN_COMMAND)
        return

    await bonuses.add_bonus(
        partner_id=partner.id,
        name=data.get("bonus_name", ""),
        condition=data.get("bonus_condition", ""),
        deadline=data.get("bonus_deadline", ""),
        promocode=promo,
    )

    await context.clear()
    await event.message.answer(
        text=messages.BONUS_ADDED,
        attachments=[commercial_partner_menu_keyboard()],
    )