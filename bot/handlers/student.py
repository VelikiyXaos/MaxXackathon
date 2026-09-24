from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.keyboards import (
    city_selection_keyboard,
    student_menu_keyboard,
    subject_selection_keyboard,
)
from bot.payloads import (
    AgreementPayload,
    CitySelectionPayload,
    MyBonusesPayload,
    MyProgressPayload,
    SubjectSelectionPayload,
)
from bot.states import StudentRegistration
from services import auth, bonuses, progress, registration



router = Router(router_id="student")


def _message_text(event: MessageCreated) -> str:
    """Возвращает текст входящего сообщения (или пустую строку)."""
    body = event.message.body
    return body.text.strip() if body and body.text else ""


@router.message_callback(AgreementPayload.filter())
async def on_accept_agreement(event: MessageCallback, context):
    """Соглашение принято — запрашиваем город."""
    await context.set_state(StudentRegistration.CITY)
    await event.send(text=messages.CITY_REQUEST)


@router.message_created(states=StudentRegistration.CITY)
async def on_city_input(event: MessageCreated, context):
    """Шаг 1: по названию города ищем регионы (субъекты), где он есть."""
    query = _message_text(event)
    subjects = await registration.search_subjects_by_city(query)

    if not subjects:
        await event.message.answer(text=messages.CITY_NOT_FOUND)
        return

    await context.update_data(city_query=query)

    if len(subjects) == 1:
        await _resolve_city_from_subject(event, context, subjects[0].id_, query)
        return

    await context.set_state(StudentRegistration.REGION)
    await event.message.answer(
        text=messages.REGION_SELECTION,
        attachments=[subject_selection_keyboard(subjects)],
    )


@router.message_callback(SubjectSelectionPayload.filter())
async def on_subject_selected(
    event: MessageCallback,
    payload: SubjectSelectionPayload,
    context,
):
    """Регион выбран из списка — ищем город внутри него."""
    data = await context.get_data()
    await _resolve_city_from_subject(
        event, context, payload.subject_id, data.get("city_query", "")
    )


async def _resolve_city_from_subject(event, context, subject_id: int, query: str):
    """Шаг 2: ищет город в выбранном регионе и переходит к учреждению."""
    cities = await registration.search_cities_in_subject(subject_id, query)

    if not cities:
        await event.send(text=messages.CITY_NOT_FOUND)
        return

    if len(cities) == 1:
        await context.update_data(city_id=cities[0].id_)
        await context.set_state(StudentRegistration.INSTITUTION)
        await event.send(text=messages.INSTITUTION_REQUEST)
        return

    await context.set_state(StudentRegistration.CITY_CHOICE)
    await event.send(
        text=messages.REGION_SELECTION,
        attachments=[city_selection_keyboard(cities)],
    )


@router.message_callback(CitySelectionPayload.filter(), states=StudentRegistration.CITY_CHOICE)
async def on_city_selected(event: MessageCallback, payload: CitySelectionPayload, context):
    """Город выбран из списка — запрашиваем учреждение."""
    await context.update_data(city_id=payload.city_id)
    await context.set_state(StudentRegistration.INSTITUTION)
    await event.send(text=messages.INSTITUTION_REQUEST)


@router.message_created(states=StudentRegistration.INSTITUTION)
async def on_institution_input(event: MessageCreated, context):
    """Обработка ввода образовательного учреждения."""
    query = _message_text(event)
    institutions = await registration.search_institutions(query)

    if not institutions:
        await event.message.answer(text=messages.INSTITUTION_NOT_FOUND)
        return

    await context.update_data(institution_id=institutions[0].id_)
    await context.set_state(StudentRegistration.FIO)
    await event.message.answer(text=messages.FIO_REQUEST)


@router.message_created(states=StudentRegistration.FIO)
async def on_fio_input(event: MessageCreated, context):
    """ФИО принято — запрашиваем год."""
    await context.update_data(fio=_message_text(event))
    await context.set_state(StudentRegistration.YEAR)
    await event.message.answer(text=messages.YEAR_REQUEST)


@router.message_created(states=StudentRegistration.YEAR)
async def on_year_input(event: MessageCreated, context):
    """Год принят — запрашиваем класс."""
    year_text = _message_text(event)
    try:
        year = int(year_text)
    except ValueError:
        year = 0 

    if year < 1 or year > 11:
        await event.message.answer (text=messages.YEAR_INVALID)
        return
    
    await context.update_data(year=year)
    await context.set_state(StudentRegistration.GROUP)
    await event.message.answer(text=messages.GROUP_REQUEST)


@router.message_created(states=StudentRegistration.GROUP)
async def on_group_input(event: MessageCreated, context):
    """Класс принята — запрашиваем логин."""
    await context.update_data(group=_message_text(event))
    await context.set_state(StudentRegistration.LOGIN)
    await event.message.answer(text=messages.LOGIN_REQUEST)


@router.message_created(states=StudentRegistration.LOGIN)
async def on_login_input(event: MessageCreated, context):
    """Логин принят — проверяем доступность и запрашиваем пароль."""
    login = _message_text(event)

    if await auth.is_login_taken(login):
        await event.message.answer(text=messages.LOGIN_TAKEN)
        return

    await context.update_data(login=login)
    await context.set_state(StudentRegistration.PASSWORD)
    await event.message.answer(text=messages.PASSWORD_REQUEST)


@router.message_created(states=StudentRegistration.PASSWORD)
async def on_password_input(event: MessageCreated, context):
    """Пароль принят — завершаем регистрацию и показываем меню учащегося."""
    data = await context.get_data()
    await context.update_data(password=_message_text(event))

    await registration.register_student(
        max_id=event.get_ids()[1] or 0,
        city_id=data.get("city_id", 0),
        institution_id=data.get("institution_id", 0),
        fio=data.get("fio", ""),
        year=data.get("year", 0),
        group=data.get("group", ""),
        login=data.get("login", ""),
        password=data.get("password", ""),
        )

    await context.clear()
    await event.message.answer(
        text=messages.STUDENT_REGISTERED,
        attachments=[student_menu_keyboard()],
    )


@router.message_callback(MyBonusesPayload.filter())
async def on_my_bonuses(event: MessageCallback):
    """Кнопка «Мои бонусы» в меню учащегося."""
    user_id = event.get_ids()[1] or 0
    student = await auth.get_student(user_id)
    if student is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    items = await bonuses.get_student_bonuses(student.id)

    if not items:
        await event.send(text=messages.MY_BONUSES_EMPTY)
    else:
        lines = [f"• {item}" for item in items]
        await event.send(text=messages.MY_BONUSES_TEMPLATE.format(bonuses="\n".join(lines)))


@router.message_callback(MyProgressPayload.filter())
async def on_my_progress(event: MessageCallback):
    """Кнопка «Мой прогресс» в меню учащегося."""
    user_id = event.get_ids()[1] or 0
    student = await auth.get_student(user_id)
    if student is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    result = await progress.get_student_progress(student.id)
    await event.send(text=messages.MY_PROGRESS_TEMPLATE.format(**result))