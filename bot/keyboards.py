import logging
from pathlib import Path

from maxapi.filters.callback_payload import CallbackPayload
from maxapi.types import (
    Attachment,
    ButtonsPayload,
    CallbackButton,
    InputMedia,
    MessageButton,
)

from bot import buttons, payloads
from services.registration import CityCandidate, SubjectCandidate

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"
AGREEMENT_FILE = ASSETS_DIR / "Пользовательское соглашение.pdf"

PROMOCODE_BUTTON_MAX = 20


def _callback_button(text: str, payload: CallbackPayload) -> CallbackButton:
    return CallbackButton(text=text, payload=payload.pack())


def _message_button(text: str) -> MessageButton:
    return MessageButton(text=text)


def _home_row() -> list[MessageButton]:
    """Ряд с кнопкой, которая отправляет боту команду /start"""
    return [_message_button(buttons.BTN_START_COMMAND)]


def home_keyboard() -> Attachment:
    """Клавиатура с единственной кнопкой /start"""
    return ButtonsPayload(buttons=[_home_row()]).pack()


def role_selection_keyboard() -> Attachment:
    """Клавиатура выбора роли: учащийся или партнёр"""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_ROLE_STUDENT,
                    payloads.RolePayload(value=payloads.ROLE_STUDENT),
                )
            ],
            [
                _callback_button(
                    buttons.BTN_ROLE_PARTNER,
                    payloads.RolePayload(value=payloads.ROLE_PARTNER),
                )
            ],
        ]
    ).pack()


def agreement_keyboard() -> Attachment:
    """Клавиатура согласия на обработку персональных данных"""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_ACCEPT_AGREEMENT,
                    payloads.AgreementPayload(),
                )
            ]
        ]
    ).pack()


def agreement_attachments() -> list[Attachment]:
    """Файл согласия и кнопка принятия в одном сообщении"""
    attachments: list[Attachment] = []
    if AGREEMENT_FILE.is_file():
        attachments.append(InputMedia(path=str(AGREEMENT_FILE)))
    else:
        logger.warning(
            "Файл согласия не найден: %s — отправляю только кнопку",
            AGREEMENT_FILE,
        )
    attachments.append(agreement_keyboard())
    return attachments


def city_selection_keyboard(cities: list[CityCandidate]) -> Attachment:
    """Клавиатура выбора города из найденных"""
    rows = [
        [
            _callback_button(
                city.name,
                payloads.CitySelectionPayload(
                    city_id=city.id_, city_name=city.name
                ),
            )
        ]
        for city in cities
    ]
    return ButtonsPayload(buttons=rows).pack()


def subject_selection_keyboard(subjects: list[SubjectCandidate]) -> Attachment:
    """Клавиатура выбора региона из найденных"""
    rows = [
        [
            _callback_button(
                subject.name,
                payloads.SubjectSelectionPayload(
                    subject_id=subject.id_, subject_name=subject.name
                ),
            )
        ]
        for subject in subjects
    ]
    return ButtonsPayload(buttons=rows).pack()


def partner_type_keyboard() -> Attachment:
    """Клавиатура выбора типа партнёра"""
    options = [
        (buttons.BTN_PARTNER_TYPE_COMMERCIAL, payloads.PARTNER_TYPE_COMMERCIAL),
        (buttons.BTN_PARTNER_TYPE_OU, payloads.PARTNER_TYPE_OU),
        (buttons.BTN_PARTNER_TYPE_ESOU, payloads.PARTNER_TYPE_ESOU),
    ]
    return ButtonsPayload(
        buttons=[
            [_callback_button(text, payloads.PartnerTypePayload(value=value))]
            for text, value in options
        ]
    ).pack()


def student_menu_keyboard() -> Attachment:
    """Главное меню учащегося"""
    return ButtonsPayload(
        buttons=[
            [_callback_button(buttons.BTN_MY_BONUSES, payloads.MyBonusesPayload())],
            [
                _callback_button(
                    buttons.BTN_AVAILABLE_BONUSES,
                    payloads.AvailableBonusesPayload(),
                )
            ],
            [
                _callback_button(
                    buttons.BTN_MY_PROGRESS, payloads.MyProgressPayload()
                )
            ],
        ]
    ).pack()


def commercial_partner_menu_keyboard() -> Attachment:
    """Главное меню коммерческого партнёра"""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_MY_BONUSES, payloads.PartnerBonusesPayload()
                )
            ],
            [_callback_button(buttons.BTN_ADD_BONUS, payloads.AddBonusPayload())],
        ]
    ).pack()


def available_bonus_keyboard(bonuses: list[dict]) -> Attachment:
    """Кнопка получения под каждым доступным бонусом и возврат назад"""
    rows = [
        [
            _callback_button(
                f"{buttons.BTN_BONUS_TAKE} {_short_promocode(item)}",
                payloads.TakeBonusPayload(bonus_id=item.get("id", 0)),
            )
        ]
        for item in bonuses
    ]
    rows.append([_callback_button(buttons.BTN_BACK, payloads.BackPayload())])
    return ButtonsPayload(buttons=rows).pack()


def _short_promocode(bonus: dict) -> str:
    """Обрезает промокод до длины, влезающей в подпись кнопки"""
    promocode = str(bonus.get("promocode", ""))
    if len(promocode) > PROMOCODE_BUTTON_MAX:
        return promocode[:PROMOCODE_BUTTON_MAX] + "…"
    return promocode


def admin_menu_keyboard() -> Attachment:
    """Главное меню администратора"""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_APPLICATIONS, payloads.ApplicationsPayload()
                )
            ],
            [
                _callback_button(
                    buttons.BTN_ADD_ADMIN, payloads.AddAdminPayload()
                )
            ],
        ]
    ).pack()


def application_decision_keyboard(application_id: int) -> Attachment:
    """Кнопки «Принять» и «Отклонить» для конкретной заявки"""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_APPLICATION_ACCEPT,
                    payloads.ApplicationDecisionPayload(
                        application_id=application_id,
                        decision=payloads.APPLICATION_ACCEPT,
                    ),
                ),
                _callback_button(
                    buttons.BTN_APPLICATION_REJECT,
                    payloads.ApplicationDecisionPayload(
                        application_id=application_id,
                        decision=payloads.APPLICATION_REJECT,
                    ),
                ),
            ]
        ]
    ).pack()


def back_keyboard() -> Attachment:
    """Клавиатура с единственной кнопкой возврата в главное меню"""
    return ButtonsPayload(
        buttons=[
            [_callback_button(buttons.BTN_BACK, payloads.BackPayload())]
        ]
    ).pack()


def role_keyboard(role: str | None) -> Attachment:
    """Клавиатура главного меню для роли или для выбора роли"""
    if role == payloads.ROLE_ADMIN:
        return admin_menu_keyboard()
    if role == payloads.ROLE_STUDENT:
        return student_menu_keyboard()
    if role == payloads.ROLE_PARTNER:
        return commercial_partner_menu_keyboard()
    return role_selection_keyboard()
