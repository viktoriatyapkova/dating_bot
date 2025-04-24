from pydantic_settings import BaseSettings
from pydantic import Field
import os
from dotenv import load_dotenv

load_dotenv() 

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(...)

    DB_HOST: str = Field(...)
    DB_PORT: int = Field(5432)
    DB_NAME: str = Field(...)
    DB_USER: str = Field(...)
    DB_PASSWORD: str = Field(...)

    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
