import asyncio
import logging

from maxapi import Bot, Dispatcher

from bot.commands import setup_commands
from bot.config import BOT_TOKEN
from bot.handlers import (
    admin_router,
    bonus_router,
    partner_router,
    setup_error_handlers,
    start_router,
    student_router,
)
from services.daily_update import daily_update_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def create_bot() -> tuple[Bot, Dispatcher]:
    """Собирает бота с роутерами и обработчиком ошибок"""
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_routers(
        start_router,
        student_router,
        partner_router,
        bonus_router,
        admin_router,
    )
    setup_error_handlers(dp)

    return bot, dp


async def main() -> None:
    """Публикует команды и уходит в бесконечный polling"""
    bot, dp = create_bot()
    await setup_commands(bot)
    logger.info("Запуск бота...")

    updater = asyncio.create_task(daily_update_loop())

    try:
        await dp.start_polling(bot)
    finally:
        updater.cancel()
        await asyncio.gather(updater, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
