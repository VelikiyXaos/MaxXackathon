from maxapi.context.state_machine import State, StatesGroup


class StudentRegistration(StatesGroup):
    """Состояния регистрации учащегося."""

    AGREEMENT = State()
    CITY = State()
    REGION = State()
    INSTITUTION = State()
    FIO = State()
    YEAR = State()
    GROUP = State()
    LOGIN = State()
    PASSWORD = State()


class PartnerRegistration(StatesGroup):
    """Состояния регистрации партнёра."""

    TYPE = State()
    PROPOSAL = State()
    CONTACTS = State()


class BonusAdding(StatesGroup):
    """Состояния добавления нового бонуса."""

    NAME = State()
    CONDITION = State()
    DEADLINE = State()
    PROMO = State()


class AdminAdding(StatesGroup):
    """Состояние добавления администратора (ожидание ID)."""

    WAIT_USER_ID = State()