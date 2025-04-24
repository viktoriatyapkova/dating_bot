from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("next"))
async def handle_next(message: Message):
    await message.answer("Следующий шаг 🚶‍♂️")
