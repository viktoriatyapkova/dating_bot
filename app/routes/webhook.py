from fastapi import APIRouter, Request
from aiogram.types import Update
from app.bot import bot, dp
from app.handlers import start  

router = APIRouter()

dp.include_router(start.router)

@router.post("/webhook")
async def process_webhook(update: dict):
    telegram_update = Update.model_validate(update)
    await dp.feed_update(bot, telegram_update)
    return {"status": "ok"}
