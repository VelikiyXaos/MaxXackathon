from bot.handlers.admin import router as admin_router
from bot.handlers.bonus import router as bonus_router
from bot.handlers.errors import setup_error_handlers
from bot.handlers.partner import router as partner_router
from bot.handlers.start import router as start_router
from bot.handlers.student import router as student_router

__all__ = [
    "admin_router",
    "bonus_router",
    "setup_error_handlers",
    "partner_router",
    "start_router",
    "student_router",
]