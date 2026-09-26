from maxapi import Router
from maxapi.filters.command import CommandStart
from maxapi.types import BotStarted, MessageCallback, MessageCreated

from bot import messages
from bot.keyboards import (
    agreement_attachments,
    partner_type_keyboard,
    role_keyboard,
)
from bot.payloads import (
    ROLE_ADMIN,
    ROLE_PARTNER,
    ROLE_STUDENT,
    BackPayload,
    RolePayload,
)
from bot.states import PartnerRegistration, StudentRegistration
from services import auth

router = Router(router_id="start")

_ROLE_TEXTS = {
    ROLE_ADMIN: messages.START_AUTHORIZED_ADMIN,
    ROLE_STUDENT: messages.START_AUTHORIZED_STUDENT,
    ROLE_PARTNER: messages.START_AUTHORIZED_PARTNER,
}


def _role_entry(role: str | None) -> tuple[str, object]:
    """Возвращает приветствие и клавиатуру для авторизованной роли.

    Если роль None — предложить выбор роли (регистрация).
    """
    return _ROLE_TEXTS.get(role, messages.START_NOT_AUTHORIZED), role_keyboard(role)


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
    
    user_id = event.get_ids()[1] or 0
    if await auth.is_registered(user_id):
        role = await auth.get_user_role(user_id)
        text, keyboard = _role_entry(role)
        await event.send(text=text, attachments=[keyboard])
        return
    
    if payload.value == ROLE_STUDENT:
        await context.set_state(StudentRegistration.AGREEMENT)
        await event.send(
            text=messages.STUDENT_AGREEMENT,
            attachments=agreement_attachments(),
        )
    elif payload.value == ROLE_PARTNER:
        await context.set_state(PartnerRegistration.TYPE)
        await event.send(
            text=messages.PARTNER_TYPE_REQUEST,
            attachments=[partner_type_keyboard()],
        )


@router.message_callback(BackPayload.filter())
async def on_back(event: MessageCallback, context):
    """Кнопка «Назад» — возвращаем главное меню по роли пользователя."""
    await context.clear()
    role = await auth.get_user_role(event.get_ids()[1] or 0)
    await event.send(attachments=[role_keyboard(role)])
