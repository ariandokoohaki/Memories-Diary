# tests/test_main.py

import os
import asyncio
import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.main import app
from app.db.base import Base
from app.db.session import get_db

# Override settings.DATABASE_URL and settings.SYNC_DATABASE_URL for testing
settings.DATABASE_URL = settings.TEST_DATABASE_URL
settings.SYNC_DATABASE_URL = "sqlite:///./test_memory_app.db"

# Remove the test database file if it exists
if os.path.exists("./test_memory_app.db"):
    os.remove("./test_memory_app.db")

# For SQLite foreign key support
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

DATABASE_URL = settings.DATABASE_URL

# Create a test database engine
async_engine = create_async_engine(
    DATABASE_URL, future=True, echo=False
)

TestingSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Override the get_db dependency
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Create the database tables before running the tests
@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop the tables after tests
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Remove the test database file
    if os.path.exists("./test_memory_app.db"):
        os.remove("./test_memory_app.db")

# Create a new event loop for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Provide a test client using AsyncClient and ASGITransport
@pytest.fixture(scope="function")
async def client():
    from httpx import AsyncClient
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=True  # Keep redirects enabled
    ) as c:
        yield c

# Now write your test functions

@pytest.mark.asyncio
async def test_register_user_success(client):
    response = await client.post(
        "/users/register",
        data={"username": "testuser", "password": "strongpassword123"}
    )
    assert response.status_code == 200  # Assuming successful registration renders a page

@pytest.mark.asyncio
async def test_register_user_existing_username(client):
    await client.post(
        "/users/register",
        data={"username": "existinguser", "password": "password123"}
    )
    response = await client.post(
        "/users/register",
        data={"username": "existinguser", "password": "password456"}
    )
    assert response.status_code == 200
    assert "User already exists" in response.text

@pytest.mark.asyncio
async def test_login_user_success(client):
    await client.post(
        "/users/register",
        data={"username": "loginuser", "password": "securepassword123"}
    )
    response = await client.post(
        "/users/login",
        data={"username": "loginuser", "password": "securepassword123"}
    )
    assert response.status_code == 200  # Assuming successful login renders a page

@pytest.mark.asyncio
async def test_login_user_wrong_credentials(client):
    await client.post(
        "/users/register",
        data={"username": "wrongloginuser", "password": "correctpassword123"}
    )
    response = await client.post(
        "/users/login",
        data={"username": "wrongloginuser", "password": "wrongpassword"}
    )
    assert response.status_code == 200
    assert "Incorrect username or password" in response.text

@pytest.mark.asyncio
async def test_login_user_nonexistent_user(client):
    response = await client.post(
        "/users/login",
        data={"username": "nonexistentuser", "password": "password123"}
    )
    assert response.status_code == 200
    assert "Incorrect username or password" in response.text

@pytest.mark.asyncio
async def test_logout_user(client):
    await client.post(
        "/users/register",
        data={"username": "logoutuser", "password": "logoutpassword123"}
    )
    await client.post(
        "/users/login",
        data={"username": "logoutuser", "password": "logoutpassword123"}
    )
    response = await client.get("/users/logout")
    # Final response after following redirects
    assert response.status_code == 200  # The response from the '/' endpoint
    # Check that a redirect happened
    assert len(response.history) > 0
    # The first response should be a redirect
    first_response = response.history[0]
    assert first_response.status_code == 302
    assert first_response.headers["Location"] == "/"

@pytest.mark.asyncio
async def test_create_memory_success(client):
    await client.post(
        "/users/register",
        data={"username": "memoryuser", "password": "memorypassword123"}
    )
    await client.post(
        "/users/login",
        data={"username": "memoryuser", "password": "memorypassword123"}
    )
    response = await client.post(
        "/memories",
        data={"title": "Test Memory", "description": "This is a test memory."}
    )
    assert response.status_code == 200  # Assuming memory creation renders a page

@pytest.mark.asyncio
async def test_create_memory_invalid_data(client):
    await client.post(
        "/users/register",
        data={"username": "invalidmemoryuser", "password": "invalidmemorypwd123"}
    )
    await client.post(
        "/users/login",
        data={"username": "invalidmemoryuser", "password": "invalidmemorypwd123"}
    )
    response = await client.post(
        "/memories",
        data={"title": "", "description": ""}
    )
    assert response.status_code == 422  # Expecting 422 Unprocessable Entity

@pytest.mark.asyncio
async def test_get_memories_authenticated(client):
    await client.post(
        "/users/register",
        data={"username": "getmemoriesuser", "password": "getmemoriespassword123"}
    )
    await client.post(
        "/users/login",
        data={"username": "getmemoriesuser", "password": "getmemoriespassword123"}
    )
    response = await client.get("/memories")
    assert response.status_code == 200
    assert "No memories found" in response.text or "Your memories" in response.text
