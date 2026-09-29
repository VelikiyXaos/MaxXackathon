from maxapi import Router
from maxapi.filters.command import CommandStart
from maxapi.types import BotStarted, MessageCallback, MessageCreated

from bot import messages
from bot.keyboards import (
    agreement_attachments,
    home_keyboard,
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


def _welcome_text(profile: auth.UserProfile) -> str:
    """Приветствие для роли пользователя: с именем, если оно есть.

    Если роль None — предложить выбор роли (регистрация).
    """
    if profile.role is None:
        return messages.START_NOT_AUTHORIZED
    if profile.role == ROLE_ADMIN:
        return messages.START_AUTHORIZED_ADMIN
    if profile.display_name is None:
        return messages.START_AUTHORIZED_NO_NAME
    return messages.START_AUTHORIZED.format(name=profile.display_name)


async def _role_entry(user_id: int) -> tuple[str, object]:
    """Возвращает приветствие и клавиатуру для роли.

    Кнопка /start не показывается ни в приветствии, ни в главном
    меню: её предлагает только подсказка для невнятного ввода.
    """
    profile = await auth.get_user_profile(user_id)
    return _welcome_text(profile), role_keyboard(profile.role)


@router.bot_started()
async def bot_started(event: BotStarted, context):
    """Срабатывает при первом открытии бота (reply-кнопка «Начать»)."""
    await context.clear()
    text, keyboard = await _role_entry(event.user.user_id)
    await event.send(text=text, attachments=[keyboard])


@router.message_created(CommandStart())
async def start_command(event: MessageCreated, context):
    """Сбрасывает состояние и открывает стартовый экран.

    Повторный /start очищает незавершённую регистрацию и начинает заново.
    """
    await context.clear()
    text, keyboard = await _role_entry(event.get_ids()[1] or 0)
    await event.message.answer(text=text, attachments=[keyboard])


@router.message_created(None)
async def on_unknown_message(event: MessageCreated):
    """Текст вне сценария — подсказка с кнопкой /start.

    None в фильтре состояний означает «состояние не задано», поэтому
    хендлер не перехватывает шаги регистрации: у них состояние задано.
    Зарегистрирован после start_command, чтобы /start обрабатывался
    как команда, а не как незнакомый текст.
    """
    await event.message.answer(
        text=messages.UNKNOWN_COMMAND,
        attachments=[home_keyboard()],
    )


@router.message_callback(RolePayload.filter())
async def on_role_selection(event: MessageCallback, payload: RolePayload, context):
    """Начало регистрации в зависимости от выбранной роли."""
    
    user_id = event.get_ids()[1] or 0
    profile = await auth.get_user_profile(user_id)
    if profile.role is not None:
        await event.send(
            text=_welcome_text(profile),
            attachments=[role_keyboard(profile.role)],
        )
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
    profile = await auth.get_user_profile(event.get_ids()[1] or 0)
    await event.send(
        text=messages.MAIN_MENU, attachments=[role_keyboard(profile.role)]
    )
