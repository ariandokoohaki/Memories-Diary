# app/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

async_engine = create_async_engine(DATABASE_URL, future=True, echo=False)
async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Synchronous engine for creating tables
from sqlalchemy import create_engine
sync_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)

# Dependency to get DB session
async def get_db():
    async with async_session() as session:
        yield session
