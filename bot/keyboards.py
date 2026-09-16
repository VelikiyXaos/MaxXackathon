from maxapi.types import Attachment, ButtonsPayload, CallbackButton

from bot.payloads import AboutPayload, HelloPayload


def main_menu_keyboard() -> Attachment:
    """Собирает inline-клавиатуру главного меню."""
    return ButtonsPayload(
        buttons=[
            [
                CallbackButton(
                    text="👋 Поздороваться",
                    payload=HelloPayload().pack(),
                )
            ],
            [
                CallbackButton(
                    text="ℹ️ О боте",
                    payload=AboutPayload().pack(),
                )
            ],
        ]
    ).pack()