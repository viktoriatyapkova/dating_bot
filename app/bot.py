import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage 
from redis.asyncio import Redis  

from app.config import settings
from app.handlers import routers

redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

storage = RedisStorage(redis=redis)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=storage)

for router in routers:
    dp.include_router(router)

async def main():
    print("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
