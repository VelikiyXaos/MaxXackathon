import asyncio
import logging

from maxapi import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.handlers import callbacks_router, setup_error_handlers, start_router
from services.daily_update import daily_update_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def create_bot() -> tuple[Bot, Dispatcher]:
    """Собирает бота: диспетчер, роутеры и обработчики ошибок."""
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_routers(start_router, callbacks_router)
    setup_error_handlers(dp)

    return bot, dp


async def main() -> None:
    bot, dp = create_bot()
    logger.info("Запуск бота...")

    # Ежедневный опрос ЭСУО и обновление бонусов в 00:00
    asyncio.create_task(daily_update_loop())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())