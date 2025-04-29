from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from ..models.sql_models import Base
from ..main import app

# PostgreSQL URL
url = URL.create(
    drivername="postgresql+asyncpg",
    username="postgres",
    password="admin",
    host="localhost",
    port=5432,
    database="postgres"
)

test_engine = create_async_engine(url, echo=True)

# Test database setup: drop & create all tables on each test run
@pytest_asyncio.fixture(scope="module")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(test_engine) as session:
        try:
            yield session
        finally:
            await session.close()


# AsyncClient fixture using ASGITransport
@pytest_asyncio.fixture(scope="module")
async def client(test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),  # Connect FastAPI app to the test client
        base_url="http://testserver"
    ) as ac:
        yield ac
