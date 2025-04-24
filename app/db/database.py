from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы успешно созданы")

@asynccontextmanager
async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session