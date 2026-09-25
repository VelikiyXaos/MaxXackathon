from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.keyboards import (
    admin_menu_keyboard,
    application_decision_keyboard,
)
from bot.payloads import (
    APPLICATION_ACCEPT,
    APPLICATION_REJECT,
    AddAdminPayload,
    ApplicationDecisionPayload,
    ApplicationsPayload,
)
from bot.states import AdminAdding
from services import applications, auth

router = Router(router_id="admin")


def _message_text(event: MessageCreated) -> str:
    """Возвращает текст входящего сообщения (или пустую строку)."""
    body = event.message.body
    return body.text.strip() if body and body.text else ""


async def _is_admin(event: MessageCallback | MessageCreated) -> bool:
    """Проверяет, что пользователь является администратором."""
    admin = await auth.get_admin(event.get_ids()[1] or 0)
    return admin is not None


@router.message_callback(ApplicationsPayload.filter())
async def on_applications(event: MessageCallback):
    """Кнопка «Список заявок» — показываем все заявки с кнопками решения."""
    if not await _is_admin(event):
        await event.send(text=messages.ACCESS_DENIED)
        return

    items = await applications.get_applications()

    if not items:
        await event.send(text=messages.APPLICATIONS_EMPTY)
        return

    for item in items:
        text = messages.APPLICATION_CARD_TEMPLATE.format(
            app_id=item.get("id", "?"),
            type=item.get("type", "?"),
            partner_name=item.get("partner_name", "?"),
            description=item.get("description", "?"),
            contact_details=item.get("contact_details", "?"),
        )
        await event.send(
            text=text,
            attachments=[application_decision_keyboard(item.get("id", 0))],
        )


@router.message_callback(ApplicationDecisionPayload.filter())
async def on_application_decision(
    event: MessageCallback,
    payload: ApplicationDecisionPayload,
):
    """Кнопки «Принять»/«Отклонить» по конкретной заявке."""
    if not await _is_admin(event):
        await event.send(text=messages.ACCESS_DENIED)
        return

    if payload.decision == APPLICATION_ACCEPT:
        await applications.accept_application(payload.application_id)
        text = messages.APPLICATION_ACCEPTED.format(app_id=payload.application_id)
    elif payload.decision == APPLICATION_REJECT:
        await applications.reject_application(payload.application_id)
        text = messages.APPLICATION_REJECTED.format(app_id=payload.application_id)
    else:
        text = messages.UNKNOWN_COMMAND

    await event.send(text=text)


@router.message_callback(AddAdminPayload.filter())
async def on_add_admin(event: MessageCallback, context):
    """Кнопка «Добавить админа» — запрашиваем ID пользователя."""
    if not await _is_admin(event):
        await event.send(text=messages.ACCESS_DENIED)
        return

    await context.set_state(AdminAdding.WAIT_USER_ID)
    await event.send(text=messages.ADD_ADMIN_ID_REQUEST)


@router.message_created(states=AdminAdding.WAIT_USER_ID)
async def on_admin_id_input(event: MessageCreated, context):
    """Ввод ID пользователя — добавляем администратора."""
    if not await _is_admin(event):
        await context.clear()
        await event.message.answer(text=messages.ACCESS_DENIED)
        return

    text = _message_text(event)
    try:
        user_id = int(text)
    except ValueError:
        await event.message.answer(text=messages.ADMIN_ID_INVALID)
        return
    
    if user_id <= 0:
        await event.message.answer(text=messages.ADMIN_ID_INVALID)
        return

    ok = await applications.add_admin(user_id)
    await context.clear()

    if ok:
        await event.message.answer(
            text=messages.ADMIN_ADDED.format(user_id=user_id),
            attachments=[admin_menu_keyboard()],
        )
    else:
        await event.message.answer(text=messages.ADMIN_NOT_ADDED)