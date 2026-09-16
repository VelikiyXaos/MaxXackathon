import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "Переменная окружения MAX_BOT_TOKEN не задана. "
        "Скопируйте .env.template в .env и укажите токен бота."
    )