# app/core/config.py

import os

from dotenv import load_dotenv
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

ENV = os.getenv("ENV", "development")

env_file = ".env" if ENV != "tests" else ".env.test"
load_dotenv(dotenv_path=env_file)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Memory App"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./data/memory_app.db"
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL", "sqlite:///./data/memory_app.db"
    )  # For synchronous engine
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL", "sqlite+aiosqlite:///./test_memory_app.db"
    )

    model_config = ConfigDict(env_file=env_file)


settings = Settings()
