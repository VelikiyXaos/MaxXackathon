"""Все тексты сообщений бота."""

# Общее
START_NOT_AUTHORIZED = (
    "Привет! Чтобы начать пользоваться ботом, выбери свою роль:"
)
START_AUTHORIZED = "{name}, с возвращением! Это ваше главное меню."
START_AUTHORIZED_NO_NAME = "Добро пожаловать! Это ваше главное меню."
START_AUTHORIZED_ADMIN = "Добро пожаловать! Вы авторизованы как администратор."
ROLE_SELECTION_PROMPT = "Выберите роль:"
UNKNOWN_COMMAND = "Я вас не понимаю. Нажмите /start, чтобы начать заново."
MAIN_MENU = "Главное меню:"

# Регистрация учащегося
STUDENT_AGREEMENT = (
    "Для использования сервиса необходимо принять пользовательское соглашение!"
    "Нажмите «Принять соглашение», чтобы продолжить."
)
CITY_REQUEST = "Введите ваш город:"
CITY_NOT_FOUND = (
    "Город не найден. Проверьте написание и попробуйте ещё раз:"
)
REGION_SELECTION = (
    "По вашему запросу найдено несколько регионов с таким городов. Выберите нужный:"
)
INSTITUTION_REQUEST = "Введите название вашего образовательного учреждения:"
INSTITUTION_NOT_FOUND = (
    "Учреждение не найдено. Проверьте название и попробуйте ещё раз:"
)
FIO_REQUEST = "Введите ваше ФИО (Фамилия Имя Отчество):"
YEAR_REQUEST = "Введите год обучения (например, 5):"
YEAR_INVALID = "Введите год обучения числом, например 5:"
GROUP_REQUEST = "Введите ваш класс:"
LOGIN_REQUEST = "Введите логин от вашего электронного дневника:"
LOGIN_TAKEN = "Данный логин уже занят! Выберите другой"
PASSWORD_REQUEST = "Введите пароль от вашего электронного дневника:"
STUDENT_REGISTERED = "Регистрация завершена, {name}!"

# Регистрация партнёра
PARTNER_TYPE_REQUEST = "Выберите тип партнёра:"
PARTNER_COMPANY_REQUEST = "Введите название компании:"
PARTNER_COMPANY_EMPTY = "Введите название компании — оно обязательно:"
PARTNER_PROPOSAL_REQUEST = (
    "Опишите ваше предложение о партнёрстве "
    "(текст предложения):"
)
PARTNER_CONTACTS_REQUEST = "Введите ваши контактные данные:"
PARTNER_APPLICATION_SENT = (
    "Ваша заявка отправлена! Компания: {company}\n"
    "Администратор рассмотрит её и свяжется с вами."
)

# Меню учащегося
MY_BONUSES_EMPTY = "Вы пока не получили ни одного бонуса."
MY_BONUSES_TEMPLATE = "Ваши бонусы:\n{bonuses}"
AVAILABLE_BONUSES_EMPTY = (
    "Пока нет доступных бонусов. Копайте опыт — новые уровни "
    "открывают новые промокоды!"
)
AVAILABLE_BONUSES_TEMPLATE = "Доступные бонусы:\n{bonuses}"
BONUS_TAKEN = "Бонус «{promocode}» получен!"
MY_PROGRESS_EMPTY = "Информация о прогрессе пока недоступна."
MY_PROGRESS_TEMPLATE = (
    "Ваш прогресс:\n"
    "- Опыт: {experience}\n"
    "- Уровень: {level}\n"
    "{bar}\n"
    "- До следующего уровня: {next_level} опыта"
)

# Шкала опыта внутри уровня
XP_BAR_WIDTH = 10
XP_BAR_FILLED = "█"
XP_BAR_EMPTY = "░"


def render_xp_bar(percent: float) -> str:
    """Строит шкалу опыта по проценту прогресса внутри уровня.

    Процент зажимается в 0..100: отрицательный опыт возможен
    (оценка «2» снимает 20 опыта), а на 15 уровне процент
    приходит уже 100. Полная шкала рисуется только на 100.
    """
    clamped = max(0.0, min(100.0, float(percent)))
    filled = int(clamped / 100 * XP_BAR_WIDTH)
    return XP_BAR_FILLED * filled + XP_BAR_EMPTY * (XP_BAR_WIDTH - filled)

# Меню коммерческого партнёра
PARTNER_BONUSES_EMPTY = "Вы пока не добавили ни одного бонуса."
PARTNER_BONUSES_TEMPLATE = "Ваши бонусы:\n{bonuses}"

# Строка списка бонусов (общая для ученика и партнёра)
BONUS_LINE_TEMPLATE = (
    "Промокод: {promocode}\n"
    "Требуемый уровень: {level}\n"
    "Действует до: {end_date}"
)
BONUS_NO_DEADLINE = "бессрочно"

# Добавление бонуса
BONUS_NAME_REQUEST = "Введите название бонуса:"
BONUS_CONDITION_REQUEST = (
    "Введите уровень от 1 до 15, с которого бонус становится доступен:"
)
BONUS_LEVEL_INVALID = "Введите целое число от 1 до 15 — например, 3:"
BONUS_DEADLINE_REQUEST = "Введите дату, до которой действует бонус (ДД.ММ.ГГГГ):"
BONUS_DEADLINE_INVALID = (
    "Не удалось распознать дату. Введите дату в формате ДД.ММ.ГГГГ, "
    "например 31.12.2026:"
)
BONUS_PROMO_REQUEST = "Введите промокод:"
BONUS_ADDED = "Бонус успешно добавлен!"

# Меню администратора
ACCESS_DENIED = "Доступ запрещён. Вы не являетесь администратором."
APPLICATIONS_EMPTY = "Список заявок пуст."
APPLICATION_CARD_TEMPLATE = (
    "Заявка №{app_id}\n"
    "Тип: {type}\n"
    "Партнёр: {partner_name}\n"
    "Описание: {description}\n"
    "Контакты: {contact_details}"
)
APPLICATION_ACCEPTED = "Заявка №{app_id} принята."
APPLICATION_REJECTED = "Заявка №{app_id} отклонена."
ADD_ADMIN_ID_REQUEST = "Введите ID пользователя, которого нужно добавить в администраторы:"
ADMIN_ADDED = "Пользователь с ID {user_id} добавлен в администраторы."
ADMIN_ALREADY_EXISTS = "Пользователь с ID {user_id} уже является администратором."
ADMIN_NOT_ADDED = "Не удалось добавить администратора. Попробуйте позже."
ADMIN_ID_INVALID = "Введите корректный ID пользователя:"