# tests/test_main.py

import pytest
from httpx import AsyncClient, ASGITransport
from app.db.session import get_db
from app.main import app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

# Create a separate test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_memory_app.db"

# Set up test engine and session
test_async_engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
TestAsyncSessionLocal = sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def initialize_database():
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session(initialize_database):
    async with TestAsyncSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.anyio
async def test_register(client):
    response = await client.post("/users/register", data={"username": "testuser", "password": "password123"})
    assert response.status_code == 302  # Expect a 302 redirect
    assert response.headers["location"] == "/users/login"

@pytest.mark.anyio
async def test_login(client):
    # First, register the user
    await client.post("/users/register", data={"username": "testuser2", "password": "password123"})
    # Now, attempt to log in
    response = await client.post("/users/login", data={"username": "testuser2", "password": "password123"})
    assert response.status_code == 302  # Redirect to /memories
    assert response.headers["location"] == "/memories"
    # Check if the access_token cookie is set
    assert "access_token" in response.cookies
