# app/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# Production database URL from settings
DATABASE_URL = settings.DATABASE_URL

# Create asynchronous engine for production
async_engine = create_async_engine(DATABASE_URL, future=True, echo=False)

# Create sessionmaker for async sessions
async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Synchronous engine for creating tables (sync for migrations, etc.)
sync_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)


# Dependency to get the async DB session
async def get_db():
    async with async_session() as session:
        yield session


# Test setup (override for testing)
# Only used during tests to ensure that the test DB is properly connected
def override_get_db(session):
    # This can be passed as a dependency override in tests
    return session
