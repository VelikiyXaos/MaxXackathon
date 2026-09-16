from maxapi import Router
from maxapi.types import MessageCallback

from bot.payloads import AboutPayload, HelloPayload

router = Router(router_id="callbacks")


@router.message_callback(HelloPayload.filter())
async def on_hello(event: MessageCallback, payload: HelloPayload):
    await event.callback.answer("Приятно познакомиться!")
    await event.send(text="Рад знакомству! 🎉")


@router.message_callback(AboutPayload.filter())
async def on_about(event: MessageCallback, payload: AboutPayload):
    await event.callback.answer("Я бот учета оценок для бонусов")
    await event.edit(
        text="Это демонстрационный бот для мессенджера MAX.",
        attachments=[],
    )