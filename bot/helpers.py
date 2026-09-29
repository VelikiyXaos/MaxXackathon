from maxapi.types import MessageCreated

from bot import messages


def message_text(event: MessageCreated) -> str:
    """Возвращает текст входящего сообщения или пустую строку"""
    body = event.message.body
    return body.text.strip() if body and body.text else ""


def bonus_line(bonus: dict) -> str:
    """Форматирует один бонус строкой для вывода списком"""
    return messages.BONUS_LINE_TEMPLATE.format(
        name=bonus.get("name") or messages.BONUS_NO_NAME,
        promocode=bonus.get("promocode", ""),
        level=bonus.get("level", 0),
        end_date=bonus.get("end_date") or messages.BONUS_NO_DEADLINE,
    )
