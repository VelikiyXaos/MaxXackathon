from maxapi import Router
from maxapi.filters.command import Command, CommandStart
from maxapi.types import BotStarted, MessageCreated

from bot.keyboards import main_menu_keyboard

router = Router(router_id="start")


@router.bot_started()
async def bot_started(event: BotStarted):
    """Срабатывает при нажатии reply-кнопки «Начать»."""
    await event.send(
        text="👋 Добро пожаловать! Я ваш новый бот.",
        attachments=[main_menu_keyboard()],
    )


@router.message_created(CommandStart())
async def start_command(event: MessageCreated):
    """commands_info: Показать приветствие."""
    await event.message.answer(
        text="Привет! Я бот в мессенджере MAX. Нажми на кнопку ниже:",
        attachments=[main_menu_keyboard()],
    )


@router.message_created(Command("help"))
async def help_command(event: MessageCreated):
    """commands_info: Показать список доступных команд."""
    await event.message.answer(
        text=(
            "Доступные команды:\n"
            "/start — приветствие\n"
            "/help — список команд"
        ),
    )