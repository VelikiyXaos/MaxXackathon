from maxapi import Router
from maxapi.filters.command import CommandStart
from maxapi.types import BotStarted, MessageCallback, MessageCreated

from bot import messages
from bot.keyboards import (
    admin_menu_keyboard,
    agreement_keyboard,
    commercial_partner_menu_keyboard,
    partner_type_keyboard,
    role_selection_keyboard,
    student_menu_keyboard,
)
from bot.payloads import (
    ROLE_ADMIN,
    ROLE_PARTNER,
    ROLE_STUDENT,
    RolePayload,
)
from bot.states import PartnerRegistration, StudentRegistration
from services import auth

router = Router(router_id="start")


def _role_entry(role: str | None) -> tuple[str, object]:
    """Возвращает приветствие и клавиатуру для авторизованной роли.

    Если роль None — предложить выбор роли (регистрация).
    """
    if role == ROLE_ADMIN:
        return messages.START_AUTHORIZED_ADMIN, admin_menu_keyboard()
    if role == ROLE_STUDENT:
        return messages.START_AUTHORIZED_STUDENT, student_menu_keyboard()
    if role == ROLE_PARTNER:
        return messages.START_AUTHORIZED_PARTNER, commercial_partner_menu_keyboard()
    return messages.START_NOT_AUTHORIZED, role_selection_keyboard()


@router.bot_started()
async def bot_started(event: BotStarted, context):
    """Срабатывает при первом открытии бота (reply-кнопка «Начать»)."""
    await context.clear()
    role = await auth.get_user_role(event.user.user_id)
    text, keyboard = _role_entry(role)
    await event.send(text=text, attachments=[keyboard])


@router.message_created(CommandStart())
async def start_command(event: MessageCreated, context):
    """Сбрасывает состояние и открывает стартовый экран.

    Повторный /start очищает незавершённую регистрацию и начинает заново.
    """
    await context.clear()
    user_id = event.get_ids()[1] or 0
    role = await auth.get_user_role(user_id)
    text, keyboard = _role_entry(role)
    await event.message.answer(text=text, attachments=[keyboard])


@router.message_callback(RolePayload.filter())
async def on_role_selection(event: MessageCallback, payload: RolePayload, context):
    """Начало регистрации в зависимости от выбранной роли."""
    if payload.value == ROLE_STUDENT:
        await context.set_state(StudentRegistration.AGREEMENT)
        await event.send(
            text=messages.STUDENT_AGREEMENT,
            attachments=[agreement_keyboard()],
        )
    elif payload.value == ROLE_PARTNER:
        await context.set_state(PartnerRegistration.TYPE)
        await event.send(
            text=messages.PARTNER_TYPE_REQUEST,
            attachments=[partner_type_keyboard()],
        )