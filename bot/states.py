from maxapi.context.state_machine import State, StatesGroup


class StudentRegistration(StatesGroup):
    AGREEMENT = State()
    CITY = State()
    REGION = State()
    CITY_CHOICE = State()
    INSTITUTION = State()
    FIO = State()
    YEAR = State()
    GROUP = State()
    LOGIN = State()
    PASSWORD = State()


class PartnerRegistration(StatesGroup):
    TYPE = State()
    COMPANY = State()
    PROPOSAL = State()
    CONTACTS = State()


class BonusAdding(StatesGroup):
    NAME = State()
    CONDITION = State()
    DEADLINE = State()
    PROMO = State()


class AdminAdding(StatesGroup):
    WAIT_USER_ID = State()
