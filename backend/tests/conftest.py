"""Global pytest fixtures for AI Panel Studio backend test suite."""

import asyncio
from typing import Any
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncByteStream, AsyncClient, Request, Response
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.database import Base
from app.main import app


class StreamingASGITransport(ASGITransport):
    """Custom ASGI Transport supporting live streaming (SSE) during test runs without blocking."""

    async def handle_async_request(self, request: Request) -> Response:
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

        class Stream(AsyncByteStream):
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

        return Response(status_code, headers=headers, stream=Stream())


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP test client fixture with live streaming support."""
    transport = StreamingASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def test_session():
    """Provides an isolated transactional async database session with in-memory SQLite and foreign keys ON."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    @event.listens_for(test_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_maker() as session:
        yield session
        await session.rollback()

    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_sessions_autouse():
    yield
    from app.infrastructure.session_manager import get_session_manager
    await get_session_manager().reset()

