import logging

from maxapi import Bot
from maxapi.types import BotCommand

logger = logging.getLogger(__name__)

BOT_COMMANDS = (
    BotCommand(
        name="start",
        description="Начать работу с ботом",
    ),
)


async def setup_commands(bot: Bot) -> None:
    """Публикует список команд, который MAX показывает при вводе «/»"""
    try:
        result = await bot.set_commands(*BOT_COMMANDS)
    except Exception as exc:
        logger.warning("Не удалось обновить список команд бота: %r", exc)
        return

    names = ", ".join(f"/{item.name}" for item in (result.commands or []))
    logger.info("Команды бота обновлены: %s", names)
