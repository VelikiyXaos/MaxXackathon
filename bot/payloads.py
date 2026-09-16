from maxapi.filters.callback_payload import CallbackPayload


class HelloPayload(CallbackPayload):
    """Кнопка «Поздороваться» в главном меню."""


class AboutPayload(CallbackPayload):
    """Кнопка «О боте» в главном меню."""