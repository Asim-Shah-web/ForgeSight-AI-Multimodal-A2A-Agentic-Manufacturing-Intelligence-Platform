"""Shared pytest fixtures: test app, test DB session, test users per role.

Tests run against a real PostgreSQL + pgvector instance identified by the
TEST_DATABASE_URL environment variable (falls back to DATABASE_URL). A
transaction is opened and rolled back around each test function so tests
never leak state into one another.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

os.environ.setdefault("DATABASE_URL", os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://forgesight:changeme@localhost:5432/forgesight_test"
))
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters-long")
os.environ.setdefault("MCP_MANUFACTURING_SERVER_URL", "http://localhost:9001")
os.environ.setdefault("MCP_DOCUMENTS_SERVER_URL", "http://localhost:9002")

from forgesight.api.main import app  # noqa: E402
from forgesight.api.security import create_access_token, hash_password  # noqa: E402
from forgesight.config import database as db_module  # noqa: E402
from forgesight.config.settings import settings  # noqa: E402
import forgesight.domain.models as models  # noqa: E402
from forgesight.domain.models.users import User, UserRole  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_test_database() -> AsyncGenerator[None, None]:
    """Create the pgvector extension and all tables once for the test session."""
    async with db_module.engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with db_module.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await db_module.engine.dispose()


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """A DB session wrapped in a transaction that's rolled back after each test."""
    async with db_module.engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
        async with session_factory() as test_session:
            yield test_session
            await test_session.rollback()
        await transaction.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """An httpx AsyncClient bound to the FastAPI app via ASGI transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


async def _create_user(session: AsyncSession, role: UserRole, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@forgesight.example",
        full_name=username.title(),
        hashed_password=hash_password("TestPassword123!"),
        role=role,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    await session.commit()
    return user


@pytest_asyncio.fixture
async def users_per_role() -> AsyncGenerator[dict[UserRole, User], None]:
    """Create one user per persona role directly against the real engine
    (committed, not rolled back) so they're visible across the test's own
    HTTP requests, which each open their own session via the app's dependency."""
    created: dict[UserRole, User] = {}
    async with db_module.AsyncSessionFactory() as db_session:
        for role in UserRole:
            username = f"fixture_{role.value}_{uuid.uuid4().hex[:6]}"
            user = await _create_user(db_session, role, username)
            created[role] = user
    yield created
    async with db_module.AsyncSessionFactory() as db_session:
        for user in created.values():
            await db_session.delete(await db_session.get(User, user.user_id))
        await db_session.commit()


def auth_headers_for(user: User) -> dict[str, str]:
    token, _ = create_access_token(subject=user.username, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_auth_headers():
    return auth_headers_for