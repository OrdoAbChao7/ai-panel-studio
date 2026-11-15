"""
E2E Test Harness Configuration & Fixtures for AI Panel Studio.
Provides async HTTP client, isolated SQLite database per test,
mock environment isolation, and SSE collector factories.
"""

import asyncio
import os
import uuid
from typing import Any, AsyncIterator, Callable, Optional
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
    try:
        from app.infrastructure.session_manager import session_manager as _sm_instance
        get_session_manager = lambda: _sm_instance
    except (ImportError, AttributeError):
        get_session_manager = lambda: None

try:
    from app.core.config import settings, get_settings
except (ImportError, AttributeError):
    try:
        from app.core.config import settings
        get_settings = lambda: settings
    except (ImportError, AttributeError):
        settings = None
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
    - Directly patches singleton settings object and environment variables
    - Clears cached pydantic settings
    """
    if settings is not None:
        monkeypatch.setattr(settings, "LLM_API_KEY", "")
        monkeypatch.setattr(settings, "LLM_BASE_URL", "")
        monkeypatch.setattr(settings, "LLM_MODEL", "mock")
        if hasattr(settings, "INTEGRITY_MODE"):
            monkeypatch.setattr(settings, "INTEGRITY_MODE", "demo")
    else:
        try:
            from app.core.config import settings as s
            monkeypatch.setattr(s, "LLM_API_KEY", "")
            monkeypatch.setattr(s, "LLM_MODEL", "mock")
        except Exception:
            pass

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
    if settings is not None:
        monkeypatch.setattr(settings, "LLM_API_KEY", "sk-mock-production-test-key-007")
        monkeypatch.setattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setattr(settings, "LLM_MODEL", "gpt-4o")
    else:
        try:
            from app.core.config import settings as s
            monkeypatch.setattr(s, "LLM_API_KEY", "sk-mock-production-test-key-007")
            monkeypatch.setattr(s, "LLM_BASE_URL", "https://api.openai.com/v1")
            monkeypatch.setattr(s, "LLM_MODEL", "gpt-4o")
        except Exception:
            pass

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
    - Drops tables and closes engine cleanly on teardown with guaranteed try...finally
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
    
    # Clean in-memory session manager if present
    async def _clean_session_manager():
        sm = get_session_manager() if callable(get_session_manager) else None
        if sm is not None:
            if hasattr(sm, "reset"):
                reset_res = sm.reset()
                if asyncio.iscoroutine(reset_res):
                    await reset_res
            elif hasattr(sm, "_sessions") and isinstance(sm._sessions, dict):
                sm._sessions.clear()
            elif hasattr(sm, "sessions") and isinstance(sm.sessions, dict):
                sm.sessions.clear()

    await _clean_session_manager()
    
    try:
        yield session_maker
    finally:
        # Teardown
        if app is not None and get_db is not None:
            app.dependency_overrides.pop(get_db, None)
        await _clean_session_manager()
        await engine.dispose()


class StreamingASGITransport(httpx.ASGITransport):
    """Custom ASGI Transport supporting live streaming (SSE) during test runs without blocking."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        queue: asyncio.Queue = asyncio.Queue()
        status_code = None
        headers = []
        started = asyncio.Event()
        response_complete = asyncio.Event()

        request_body_chunks = request.stream.__aiter__()
        request_complete = False

        async def receive() -> dict[str, Any]:
            nonlocal request_complete
            if request_complete:
                await response_complete.wait()
                return {"type": "http.disconnect"}
            try:
                body = await request_body_chunks.__anext__()
            except StopAsyncIteration:
                request_complete = True
                return {"type": "http.request", "body": b"", "more_body": False}
            return {"type": "http.request", "body": body, "more_body": True}

        async def send(message: dict[str, Any]) -> None:
            nonlocal status_code, headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = message.get("headers", [])
                started.set()
            elif message["type"] == "http.response.body":
                await queue.put(message.get("body", b""))
                if not message.get("more_body", False):
                    response_complete.set()
                    await queue.put(None)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": request.method,
            "headers": [(k.lower(), v) for (k, v) in request.headers.raw],
            "scheme": request.url.scheme,
            "path": request.url.path,
            "raw_path": request.url.raw_path.split(b"?")[0],
            "query_string": request.url.query,
            "server": (request.url.host, request.url.port),
            "client": self.client,
            "root_path": self.root_path,
        }
        app_task = asyncio.create_task(self.app(scope, receive, send))

        await started.wait()

        class Stream(httpx.AsyncByteStream):
            async def __aiter__(self):
                while True:
                    chunk = await queue.get()
                    if chunk is None:
                        break
                    if chunk:
                        yield chunk

            async def aclose(self):
                response_complete.set()
                app_task.cancel()
                try:
                    await app_task
                except (asyncio.CancelledError, Exception):
                    pass

        return httpx.Response(status_code, headers=headers, stream=Stream())


@pytest.fixture
async def async_client(test_db) -> AsyncIterator[httpx.AsyncClient]:
    """
    Asynchronous HTTP client bound to FastAPI application via StreamingASGITransport.
    Executes in-memory at maximum speed while respecting complete HTTP and SSE streaming semantics.
    """
    assert app is not None, "FastAPI app could not be imported from app.main"
    transport = StreamingASGITransport(app=app)
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
