from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.payloads import AddBonusPayload, MyBonusesPayload, PartnerTypePayload
from bot.states import BonusAdding, PartnerRegistration
from services import bonuses, registration

router = Router(router_id="partner")


def _message_text(event: MessageCreated) -> str:
    """Возвращает текст входящего сообщения (или пустую строку)."""
    body = event.message.body
    return body.text.strip() if body and body.text else ""


@router.message_callback(PartnerTypePayload.filter())
async def on_partner_type(event: MessageCallback, payload: PartnerTypePayload, context):
    """Тип партнёра выбран — запрашиваем текст предложения."""
    await context.update_data(partner_type=payload.value)
    await context.set_state(PartnerRegistration.PROPOSAL)
    await event.send(text=messages.PARTNER_PROPOSAL_REQUEST)


@router.message_created(states=PartnerRegistration.PROPOSAL)
async def on_proposal_input(event: MessageCreated, context):
    """Предложение принято — запрашиваем контакты."""
    await context.update_data(proposal=_message_text(event))
    await context.set_state(PartnerRegistration.CONTACTS)
    await event.message.answer(text=messages.PARTNER_CONTACTS_REQUEST)


@router.message_created(states=PartnerRegistration.CONTACTS)
async def on_contacts_input(event: MessageCreated, context):
    """Контакты приняты — отправляем заявку партнёра."""
    data = await context.get_data()
    await context.update_data(contacts=_message_text(event))

    await registration.submit_partner_application(
        max_id=event.get_ids()[1] or 0,
        partner_type=data.get("partner_type", ""),
        proposal=data.get("proposal", ""),
        contacts=data.get("contacts", ""),
    )

    await context.clear()
    await event.message.answer(text=messages.PARTNER_APPLICATION_SENT)


@router.message_callback(MyBonusesPayload.filter())
async def on_my_bonuses(event: MessageCallback):
    """Кнопка «Мои бонусы» в меню коммерческого партнёра."""
    user_id = event.get_ids()[1] or 0
    items = await bonuses.get_partner_bonuses(user_id)

    if not items:
        await event.send(text=messages.PARTNER_BONUSES_EMPTY)
    else:
        lines = [f"• {item}" for item in items]
        await event.send(
            text=messages.PARTNER_BONUSES_TEMPLATE.format(
                bonuses="\n".join(lines)
            )
        )


@router.message_callback(AddBonusPayload.filter())
async def on_add_bonus(event: MessageCallback, context):
    """Кнопка «Добавить бонус» — начинаем FSM добавления бонуса."""
    await context.set_state(BonusAdding.NAME)
    await event.send(text=messages.BONUS_NAME_REQUEST)