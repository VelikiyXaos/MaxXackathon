import logging

from maxapi import Dispatcher, ErrorEvent

logger = logging.getLogger(__name__)


def setup_error_handlers(dp: Dispatcher) -> None:
    @dp.errors()
    async def on_error(event: ErrorEvent) -> None:
        logger.error(
            "Необработанная ошибка при обработке %s: %s",
            event.update.update_type,
            event.exception,
            exc_info=event.exception,
        )