from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.helpers import bonus_line, message_text
from bot.keyboards import back_keyboard
from bot.payloads import (
    AddBonusPayload,
    PartnerBonusesPayload,
    PartnerTypePayload,
)
from bot.states import BonusAdding, PartnerRegistration
from services import auth, bonuses, registration

router = Router(router_id="partner")


@router.message_callback(PartnerTypePayload.filter())
async def on_partner_type(
    event: MessageCallback,
    payload: PartnerTypePayload,
    context,
):
    """Тип партнёра выбран: запрашиваем название компании"""
    await context.update_data(partner_type=payload.value)
    await context.set_state(PartnerRegistration.COMPANY)
    await event.send(text=messages.PARTNER_COMPANY_REQUEST)


@router.message_created(states=PartnerRegistration.COMPANY)
async def on_company_input(event: MessageCreated, context):
    """Название компании принято: запрашиваем текст предложения"""
    company = message_text(event)

    if not company:
        await event.message.answer(text=messages.PARTNER_COMPANY_EMPTY)
        return

    await context.update_data(company=company)
    await context.set_state(PartnerRegistration.PROPOSAL)
    await event.message.answer(text=messages.PARTNER_PROPOSAL_REQUEST)


@router.message_created(states=PartnerRegistration.PROPOSAL)
async def on_proposal_input(event: MessageCreated, context):
    """Предложение принято: запрашиваем контакты"""
    await context.update_data(proposal=message_text(event))
    await context.set_state(PartnerRegistration.CONTACTS)
    await event.message.answer(text=messages.PARTNER_CONTACTS_REQUEST)


@router.message_created(states=PartnerRegistration.CONTACTS)
async def on_contacts_input(event: MessageCreated, context):
    """Контакты приняты: сохраняем заявку партнёра"""
    data = await context.get_data()
    company = data.get("company", "")
    contacts = message_text(event)
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


@router.message_callback(PartnerBonusesPayload.filter())
async def on_my_bonuses(event: MessageCallback):
    """Показывает бонусы, созданные партнёром"""
    user_id = event.get_ids()[1] or 0
    if await auth.get_partner(user_id) is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    items = await bonuses.get_partner_bonuses(user_id)
    if not items:
        await event.send(
            text=messages.PARTNER_BONUSES_EMPTY,
            attachments=[back_keyboard()],
        )
        return

    lines = "\n".join(f"• {bonus_line(item)}" for item in items)
    await event.send(
        text=messages.PARTNER_BONUSES_TEMPLATE.format(bonuses=lines),
        attachments=[back_keyboard()],
    )


@router.message_callback(AddBonusPayload.filter())
async def on_add_bonus(event: MessageCallback, context):
    """Начинает добавление нового бонуса"""
    await context.set_state(BonusAdding.NAME)
    await event.send(text=messages.BONUS_NAME_REQUEST)
