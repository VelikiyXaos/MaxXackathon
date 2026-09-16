from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.errors import setup_error_handlers
from bot.handlers.start import router as start_router

__all__ = [
    "callbacks_router",
    "setup_error_handlers",
    "start_router",
]