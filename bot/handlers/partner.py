from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.keyboards import back_keyboard
from bot.payloads import AddBonusPayload, MyBonusesPayload, PartnerTypePayload
from bot.states import BonusAdding, PartnerRegistration
from services import auth, bonuses, registration

router = Router(router_id="partner")


def _message_text(event: MessageCreated) -> str:
    """Возвращает текст входящего сообщения (или пустую строку)."""
    body = event.message.body
    return body.text.strip() if body and body.text else ""


@router.message_callback(PartnerTypePayload.filter())
async def on_partner_type(event: MessageCallback, payload: PartnerTypePayload, context):
    """Тип партнёра выбран — запрашиваем название компании."""
    await context.update_data(partner_type=payload.value)
    await context.set_state(PartnerRegistration.COMPANY)
    await event.send(text=messages.PARTNER_COMPANY_REQUEST)


@router.message_created(states=PartnerRegistration.COMPANY)
async def on_company_input(event: MessageCreated, context):
    """Название компании принято — запрашиваем текст предложения."""
    company = _message_text(event)

    if not company:
        await event.message.answer(text=messages.PARTNER_COMPANY_EMPTY)
        return

    await context.update_data(company=company)
    await context.set_state(PartnerRegistration.PROPOSAL)
    await event.message.answer(text=messages.PARTNER_PROPOSAL_REQUEST)


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
    company = data.get("company", "")
    contacts = _message_text(event)
    await context.update_data(contacts=contacts)

    await registration.submit_partner_application(
        max_id=event.get_ids()[1] or 0,
        partner_type=data.get("partner_type", ""),
        partner_name=company,
        proposal=data.get("proposal", ""),
        contacts=contacts,
    )

    await context.clear()
    await event.message.answer(
        text=messages.PARTNER_APPLICATION_SENT.format(company=company)
    )


@router.message_callback(MyBonusesPayload.filter())
async def on_my_bonuses(event: MessageCallback):
    """Кнопка «Мои бонусы» в меню коммерческого партнёра."""
    user_id = event.get_ids()[1] or 0
    partner = await auth.get_partner(user_id)
    if partner is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    items = await bonuses.get_partner_bonuses(partner.id)

    if not items:
        await event.send(
            text=messages.PARTNER_BONUSES_EMPTY,
            attachments=[back_keyboard()],
        )
    else:
        lines = [f"• {item}" for item in items]
        await event.send(
            text=messages.PARTNER_BONUSES_TEMPLATE.format(
                bonuses="\n".join(lines)
            ),
            attachments=[back_keyboard()],
        )


@router.message_callback(AddBonusPayload.filter())
async def on_add_bonus(event: MessageCallback, context):
    """Кнопка «Добавить бонус» — начинаем FSM добавления бонуса."""
    await context.set_state(BonusAdding.NAME)
    await event.send(text=messages.BONUS_NAME_REQUEST)