import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ANTHROPIC_API_KEY", "")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.core import db as db_module
from app.main import app


@pytest_asyncio.fixture
async def test_db():
    """A fresh in-memory MongoDB per test, wired into the app's get_db dependency
    so router code runs unmodified against it (no real MongoDB needed for tests)."""
    mock_client = AsyncMongoMockClient()
    database = mock_client["softlifesociety_test"]

    app.dependency_overrides[db_module.get_db] = lambda: database
    await db_module.ensure_indexes(database)

    yield database

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    async def _signup(name: str = "Destini Test", email: str = "destini@example.com", password: str = "supersecret1"):
        response = await client.post("/auth/signup", json={"name": name, "email": email, "password": password})
        assert response.status_code == 201, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _signup
