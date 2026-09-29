from maxapi import Router
from maxapi.types import MessageCallback, MessageCreated

from bot import messages
from bot.helpers import bonus_line, message_text
from bot.keyboards import (
    available_bonus_keyboard,
    back_keyboard,
    city_selection_keyboard,
    student_menu_keyboard,
    subject_selection_keyboard,
)
from bot.payloads import (
    AgreementPayload,
    AvailableBonusesPayload,
    CitySelectionPayload,
    MyBonusesPayload,
    MyProgressPayload,
    SubjectSelectionPayload,
    TakeBonusPayload,
)
from bot.states import StudentRegistration
from services import auth, bonuses, progress, registration

router = Router(router_id="student")


async def _resolve_city_from_subject(event, context, subject_id: int, query: str):
    """Ищет город в выбранном регионе и переходит к выбору учреждения"""
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


@router.message_callback(AgreementPayload.filter())
async def on_accept_agreement(event: MessageCallback, context):
    """Соглашение принято: запрашиваем город"""
    await context.set_state(StudentRegistration.CITY)
    await event.send(text=messages.CITY_REQUEST)


@router.message_created(states=StudentRegistration.CITY)
async def on_city_input(event: MessageCreated, context):
    """Ищет регионы, в которых есть город с таким названием"""
    query = message_text(event)
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
    """Регион выбран из списка: ищем город внутри него"""
    data = await context.get_data()
    await _resolve_city_from_subject(
        event, context, payload.subject_id, data.get("city_query", "")
    )


@router.message_callback(
    CitySelectionPayload.filter(),
    states=StudentRegistration.CITY_CHOICE,
)
async def on_city_selected(
    event: MessageCallback,
    payload: CitySelectionPayload,
    context,
):
    """Город выбран из списка: запрашиваем учреждение"""
    await context.update_data(city_id=payload.city_id)
    await context.set_state(StudentRegistration.INSTITUTION)
    await event.send(text=messages.INSTITUTION_REQUEST)


@router.message_created(states=StudentRegistration.INSTITUTION)
async def on_institution_input(event: MessageCreated, context):
    """Ищет образовательное учреждение по введённому названию"""
    query = message_text(event)
    institutions = await registration.search_institutions(query)

    if not institutions:
        await event.message.answer(text=messages.INSTITUTION_NOT_FOUND)
        return

    await context.update_data(institution_id=institutions[0].id_)
    await context.set_state(StudentRegistration.FIO)
    await event.message.answer(text=messages.FIO_REQUEST)


@router.message_created(states=StudentRegistration.FIO)
async def on_fio_input(event: MessageCreated, context):
    """ФИО принято: запрашиваем год обучения"""
    await context.update_data(fio=message_text(event))
    await context.set_state(StudentRegistration.YEAR)
    await event.message.answer(text=messages.YEAR_REQUEST)


@router.message_created(states=StudentRegistration.YEAR)
async def on_year_input(event: MessageCreated, context):
    """Год принят: запрашиваем класс"""
    try:
        year = int(message_text(event))
    except ValueError:
        year = 0

    if not 1 <= year <= 11:
        await event.message.answer(text=messages.YEAR_INVALID)
        return

    await context.update_data(year=year)
    await context.set_state(StudentRegistration.GROUP)
    await event.message.answer(text=messages.GROUP_REQUEST)


@router.message_created(states=StudentRegistration.GROUP)
async def on_group_input(event: MessageCreated, context):
    """Класс принят: запрашиваем логин"""
    await context.update_data(group=message_text(event))
    await context.set_state(StudentRegistration.LOGIN)
    await event.message.answer(text=messages.LOGIN_REQUEST)


@router.message_created(states=StudentRegistration.LOGIN)
async def on_login_input(event: MessageCreated, context):
    """Логин принят: проверяем занятость и запрашиваем пароль"""
    login = message_text(event)

    if await auth.is_login_taken(login):
        await event.message.answer(text=messages.LOGIN_TAKEN)
        return

    await context.update_data(login=login)
    await context.set_state(StudentRegistration.PASSWORD)
    await event.message.answer(text=messages.PASSWORD_REQUEST)


@router.message_created(states=StudentRegistration.PASSWORD)
async def on_password_input(event: MessageCreated, context):
    """Пароль принят: завершаем регистрацию и открываем меню"""
    data = await context.get_data()
    password = message_text(event)
    await context.update_data(password=password)

    try:
        student = await registration.register_student(
            max_id=event.get_ids()[1] or 0,
            city_id=data.get("city_id", 0),
            institution_id=data.get("institution_id", 0),
            fio=data.get("fio", ""),
            year=data.get("year", 0),
            group=data.get("group", ""),
            login=data.get("login", ""),
            password=password,
        )
    except registration.RegistrationError as exc:
        await event.message.answer(text=str(exc))
        return

    await context.clear()
    await event.message.answer(
        text=messages.STUDENT_REGISTERED.format(
            name=f"{student.surname} {student.name}"
        ),
        attachments=[student_menu_keyboard()],
    )


@router.message_callback(MyBonusesPayload.filter())
async def on_my_bonuses(event: MessageCallback):
    """Показывает бонусы, полученные учеником"""
    user_id = event.get_ids()[1] or 0
    if await auth.get_student(user_id) is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    items = await bonuses.get_student_bonuses(user_id)
    if not items:
        await event.send(
            text=messages.MY_BONUSES_EMPTY,
            attachments=[back_keyboard()],
        )
        return

    lines = "\n".join(f"• {bonus_line(item)}" for item in items)
    await event.send(
        text=messages.MY_BONUSES_TEMPLATE.format(bonuses=lines),
        attachments=[back_keyboard()],
    )


@router.message_callback(AvailableBonusesPayload.filter())
async def on_available_bonuses(event: MessageCallback):
    """Показывает бонусы, доступные при текущем опыте"""
    user_id = event.get_ids()[1] or 0
    if await auth.get_student(user_id) is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    items = await bonuses.get_available_bonuses(user_id)
    if not items:
        await event.send(
            text=messages.AVAILABLE_BONUSES_EMPTY,
            attachments=[back_keyboard()],
        )
        return

    lines = "\n".join(f"• {bonus_line(item)}" for item in items)
    await event.send(
        text=messages.AVAILABLE_BONUSES_TEMPLATE.format(bonuses=lines),
        attachments=[available_bonus_keyboard(items)],
    )


@router.message_callback(TakeBonusPayload.filter())
async def on_take_bonus(event: MessageCallback, payload: TakeBonusPayload):
    """Выдаёт бонус и показывает его промокод"""
    user_id = event.get_ids()[1] or 0
    if await auth.get_student(user_id) is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    try:
        bonus = await bonuses.issue_bonus(user_id, payload.bonus_id)
    except ValueError as exc:
        await event.send(text=str(exc), attachments=[back_keyboard()])
        return

    await event.send(
        text=messages.BONUS_TAKEN.format(promocode=bonus["promocode"]),
        attachments=[back_keyboard()],
    )


@router.message_callback(MyProgressPayload.filter())
async def on_my_progress(event: MessageCallback):
    """Показывает опыт, уровень и шкалу прогресса"""
    user_id = event.get_ids()[1] or 0
    if await auth.get_student(user_id) is None:
        await event.send(text=messages.UNKNOWN_COMMAND)
        return

    result = await progress.get_student_progress(user_id)
    if result is None:
        await event.send(text=messages.MY_PROGRESS_EMPTY)
        return

    await event.send(
        text=messages.MY_PROGRESS_TEMPLATE.format(
            bar=messages.render_xp_bar(result["progress_percent"]),
            **result,
        ),
        attachments=[back_keyboard()],
    )
