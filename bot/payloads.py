from maxapi.filters.callback_payload import CallbackPayload

ROLE_STUDENT = "student"
ROLE_PARTNER = "partner"
ROLE_ADMIN = "admin"

PARTNER_TYPE_COMMERCIAL = "commercial"
PARTNER_TYPE_OU = "ou"
PARTNER_TYPE_ESOU = "esou"

APPLICATION_ACCEPT = "accept"
APPLICATION_REJECT = "reject"


class RolePayload(CallbackPayload):
    """Выбор роли при старте регистрации."""

    value: str


class AgreementPayload(CallbackPayload):
    """Кнопка «Принять соглашение»."""


class CitySelectionPayload(CallbackPayload):
    """Выбор города из списка найденных."""

    city_id: int
    city_name: str


class SubjectSelectionPayload(CallbackPayload):
    """Выбор региона (субъекта) из списка найденных."""

    subject_id: int
    subject_name: str


class PartnerTypePayload(CallbackPayload):
    """Выбор типа партнёра."""

    value: str


class MyBonusesPayload(CallbackPayload):
    """Кнопка «Мои бонусы»."""


class MyProgressPayload(CallbackPayload):
    """Кнопка «Мой прогресс»."""


class AddBonusPayload(CallbackPayload):
    """Кнопка «Добавить бонус»."""


class ApplicationsPayload(CallbackPayload):
    """Кнопка «Список заявок»."""


class AddAdminPayload(CallbackPayload):
    """Кнопка «Добавить админа»."""


class ApplicationDecisionPayload(CallbackPayload):
    """Решение администратора по конкретной заявке."""

    application_id: int
    decision: str