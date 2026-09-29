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
    value: str


class AgreementPayload(CallbackPayload):
    pass


class CitySelectionPayload(CallbackPayload):
    city_id: int
    city_name: str


class SubjectSelectionPayload(CallbackPayload):
    subject_id: int
    subject_name: str


class PartnerTypePayload(CallbackPayload):
    value: str


class MyBonusesPayload(CallbackPayload):
    pass


class PartnerBonusesPayload(CallbackPayload):
    pass


class AvailableBonusesPayload(CallbackPayload):
    pass


class TakeBonusPayload(CallbackPayload):
    bonus_id: int


class MyProgressPayload(CallbackPayload):
    pass


class AddBonusPayload(CallbackPayload):
    pass


class ApplicationsPayload(CallbackPayload):
    pass


class AddAdminPayload(CallbackPayload):
    pass


class ApplicationDecisionPayload(CallbackPayload):
    application_id: int
    decision: str


class BackPayload(CallbackPayload):
    pass
