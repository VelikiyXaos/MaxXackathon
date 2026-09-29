from __future__ import annotations

import logging
import os

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv(override=False)

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


class DecryptionError(RuntimeError):
    pass


class EncryptionKeyError(RuntimeError):
    pass


def reset_cache() -> None:
    """Сбрасывает закэшированный шифровальщик"""
    global _fernet
    _fernet = None


def get_fernet() -> Fernet:
    """Отдаёт шифровальщик по ключу EGAS_ENCRYPTION_KEY из окружения"""
    global _fernet
    if _fernet is not None:
        return _fernet

    raw = os.getenv("EGAS_ENCRYPTION_KEY", "").strip()
    if not raw:
        raise EncryptionKeyError(
            "Переменная окружения EGAS_ENCRYPTION_KEY не задана. "
            "Скопируйте .env.example в .env и сгенерируйте ключ командой "
            "python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"."
        )

    try:
        _fernet = Fernet(raw.encode())
    except (ValueError, TypeError) as exc:
        raise EncryptionKeyError(
            "EGAS_ENCRYPTION_KEY имеет неверный формат: нужен ключ Fernet "
            "из 44 символов"
        ) from exc

    logger.info("Ключ шифрования паролей загружен из окружения")
    return _fernet


def encrypt(plaintext: str) -> str:
    """Шифрует пароль перед записью в базу"""
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Расшифровывает пароль перед отправкой в ЭСУО"""
    try:
        return get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError(
            "Не удалось расшифровать пароль: значение зашифровано другим "
            "ключом либо повреждено"
        ) from exc
