"""
E2E Test Harness Configuration & Fixtures for AI Panel Studio.
Provides async HTTP client, isolated SQLite database per test,
mock environment isolation, and SSE collector factories.
"""

import asyncio
import os
import uuid
from typing import AsyncIterator, Callable, Optional
import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

try:
    from app.main import app
except (ImportError, AttributeError):
    app = None

try:
    from app.infrastructure.database import Base, get_db
except (ImportError, AttributeError):
    Base = None
    get_db = None

try:
    from app.infrastructure.session_manager import get_session_manager
except (ImportError, AttributeError):
    get_session_manager = lambda: None

try:
    from app.core.config import get_settings
except (ImportError, AttributeError):
    get_settings = lambda: None

from .sse_helper import SSECollector, SSEStreamReader


@pytest.fixture(scope="session")
def anyio_backend():
    """Ensure anyio / pytest-asyncio backend is standard asyncio."""
    return "asyncio"


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """
    Ensure Mock LLM mode by default for all automated E2E tests:
    - Zero external network requests
    - Zero API cost
    - Deterministic 5-domain mock debate execution
    - Clears cached pydantic settings
    """
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_BASE_URL", "")
    monkeypatch.setenv("LLM_MODEL", "mock")
    monkeypatch.setenv("INTEGRITY_MODE", "demo")
    
    # Invalidate settings cache if using lru_cache
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()


@pytest.fixture
def with_real_llm_env(monkeypatch):
    """
    Fixture specifically for testing real LLM credential loading & isolation (F19).
    Injects dummy credentials that must never be leaked to client bundles or responses.
    """
    monkeypatch.setenv("LLM_API_KEY", "sk-mock-production-test-key-007")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()


@pytest.fixture
async def test_db(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """
    Creates an isolated temporary SQLite database for each test:
    - Unique database file path in pytest's tmp_path
    - Fully creates schema tables via Base.metadata.create_all
    - Overrides FastAPI get_db dependency
    - Resets SessionManager in-memory registry to prevent state leakage
    - Drops tables and closes engine cleanly on teardown
    """
    db_filename = tmp_path / f"test_e2e_{uuid.uuid4().hex[:8]}.db"
    db_url = f"sqlite+aiosqlite:///{db_filename.as_posix()}"
    
    engine = create_async_engine(db_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    # Initialize schema
    if Base is not None and hasattr(Base, "metadata"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    if app is not None and get_db is not None:
        app.dependency_overrides[get_db] = override_get_db
    
    # Reset in-memory session manager if present
    session_mgr = get_session_manager() if callable(get_session_manager) else None
    if session_mgr and hasattr(session_mgr, "reset"):
        reset_res = session_mgr.reset()
        if asyncio.iscoroutine(reset_res):
            await reset_res
        
    yield session_maker
    
    # Teardown
    if app is not None and get_db is not None:
        app.dependency_overrides.pop(get_db, None)
    if session_mgr and hasattr(session_mgr, "reset"):
        reset_res = session_mgr.reset()
        if asyncio.iscoroutine(reset_res):
            await reset_res
    await engine.dispose()


@pytest.fixture
async def async_client(test_db) -> AsyncIterator[httpx.AsyncClient]:
    """
    Asynchronous HTTP client bound to FastAPI application via ASGITransport.
    Executes in-memory at maximum speed while respecting complete HTTP semantics.
    """
    assert app is not None, "FastAPI app could not be imported from app.main"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=httpx.Timeout(30.0, connect=5.0),
    ) as client:
        yield client


@pytest.fixture
def sse_reader_factory(async_client: httpx.AsyncClient) -> Callable[..., SSEStreamReader]:
    """Factory returning an SSEStreamReader context manager for a given discussion ID."""
    def _create(discussion_id: str, last_event_id: Optional[str] = None, timeout: float = 30.0) -> SSEStreamReader:
        url = f"/api/discussions/{discussion_id}/events"
        return SSEStreamReader(client=async_client, url=url, last_event_id=last_event_id, timeout=timeout)
    return _create


@pytest.fixture
def sse_collector_factory(async_client: httpx.AsyncClient) -> Callable[..., SSECollector]:
    """Factory returning an active background SSECollector for a given discussion ID."""
    def _create(discussion_id: str, last_event_id: Optional[str] = None, timeout: float = 30.0) -> SSECollector:
        url = f"/api/discussions/{discussion_id}/events"
        return SSECollector(client=async_client, url=url, last_event_id=last_event_id, timeout=timeout)
    return _create
