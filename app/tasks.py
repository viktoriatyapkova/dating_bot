from celery import Celery
from app.config import settings
import asyncio

celery_app = Celery(
    "tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
)

@celery_app.task
def send_like_notification(user_id: int, liker_name: str):
    from app.bot import bot

    async def send_notification():
        text = f"Кому-то понравилась ваша анкета ❤️"
        await bot.send_message(chat_id=user_id, text=text)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_notification())
