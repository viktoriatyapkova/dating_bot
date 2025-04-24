from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.bot import bot, dp
from app.db.database import create_tables
import asyncio
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()

    asyncio.create_task(run_bot())
    
    yield

    await bot.session.close()

async def run_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

app = FastAPI(
    title="Dating Bot Backend",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)