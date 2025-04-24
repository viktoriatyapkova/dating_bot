from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

WELCOME_MESSAGE = """
👋 Привет! Рад тебя видеть в боте знакомств!

💞 Здесь ты сможешь найти интересных людей для общения, дружбы или чего-то большего 😉

Чтобы начать, заполги анкету о себе — так мы сможем подобрать тебе подходящих собеседников.

Напиши /registr и вперед к новым знакомствам! 🚀
"""

@router.message(Command("start"))
async def handle_start(message: Message):
    await message.answer(WELCOME_MESSAGE)
