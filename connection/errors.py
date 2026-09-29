from __future__ import annotations


class EgasError(RuntimeError):
    """Ошибка общения с сервером ЭСУО (сеть, HTTP, неожиданный формат)"""


class EgasAuthError(EgasError):
    """Не удалось авторизоваться в ЭСУО (нет пароля, отказ сервера)"""


class EgasStudentNotFoundError(EgasError):
    """У логина в ЭСУО нет ученического профиля"""
