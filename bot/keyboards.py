from maxapi.types import (
    Attachment,
    ButtonsPayload,
    CallbackButton,
    MessageButton,
)

from bot import buttons, payloads


def _callback_button(text: str, payload: payloads.CallbackPayload) -> CallbackButton:
    return CallbackButton(text=text, payload=payload.pack())


def _message_button(text: str) -> MessageButton:
    return MessageButton(text=text)


def _home_row() -> list[MessageButton]:
    """Ряд с кнопкой, отправляющей команду /start.

    Нажатие MessageButton присылает боту обычное сообщение "/start",
    поэтому срабатывает существующий хендлер команды /start.
    """
    return [_message_button(buttons.BTN_START_COMMAND)]


def role_selection_keyboard() -> Attachment:
    """Inline-клавиатура выбора роли: учащийся / партнёр."""
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
    """Inline-клавиатура соглашения на обработку персональных данных."""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_ACCEPT_AGREEMENT,
                    payloads.AgreementPayload(),
                )
            ],
        ]
    ).pack()


def city_selection_keyboard(cities: list) -> Attachment:
    """Inline-клавиатура выбора города/региона из найденных."""
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


def subject_selection_keyboard(subjects: list) -> Attachment:
    """Inline-клавиатура выбора региона (субъекта) из найденных."""
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
    """Inline-клавиатура выбора типа партнёра."""
    options = [
        (buttons.BTN_PARTNER_TYPE_COMMERCIAL, payloads.PARTNER_TYPE_COMMERCIAL),
        (buttons.BTN_PARTNER_TYPE_OU, payloads.PARTNER_TYPE_OU),
        (buttons.BTN_PARTNER_TYPE_ESOU, payloads.PARTNER_TYPE_ESOU),
    ]
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    text, payloads.PartnerTypePayload(value=value)
                )
            ]
            for text, value in options
        ]
    ).pack()


def student_menu_keyboard() -> Attachment:
    """Главное меню учащегося."""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_MY_BONUSES, payloads.MyBonusesPayload()
                )
            ],
            [
                _callback_button(
                    buttons.BTN_MY_PROGRESS, payloads.MyProgressPayload()
                )
            ],
            _home_row(),
        ]
    ).pack()


def commercial_partner_menu_keyboard() -> Attachment:
    """Главное меню коммерческого партнёра."""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_MY_BONUSES, payloads.MyBonusesPayload()
                )
            ],
            [
                _callback_button(
                    buttons.BTN_ADD_BONUS, payloads.AddBonusPayload()
                )
            ],
            _home_row(),
        ]
    ).pack()


def admin_menu_keyboard() -> Attachment:
    """Главное меню администратора."""
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
            _home_row(),
        ]
    ).pack()


def application_decision_keyboard(application_id: int) -> Attachment:
    """Кнопки «Принять»/«Отклонить» для конкретной заявки."""
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
            ],
        ]
    ).pack()


def back_keyboard() -> Attachment:
    """Клавиатура с единственной кнопкой возврата в главное меню."""
    return ButtonsPayload(
        buttons=[
            [
                _callback_button(
                    buttons.BTN_BACK, payloads.BackPayload()
                )
            ],
        ]
    ).pack()


def role_keyboard(role: str | None) -> Attachment:
    """Клавиатура главного меню для роли (выбор роли, если роль None)."""
    if role == payloads.ROLE_ADMIN:
        return admin_menu_keyboard()
    if role == payloads.ROLE_STUDENT:
        return student_menu_keyboard()
    if role == payloads.ROLE_PARTNER:
        return commercial_partner_menu_keyboard()
    return role_selection_keyboard()
