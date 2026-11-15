"""Asynchronous SQLite Database Engine, Pragmas, and Session Factory."""

from typing import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base class."""

    pass


# Asynchronous SQLite engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    future=True,
)


@event.listens_for(engine.sync_engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure critical SQLite pragmas upon connection:

    - Foreign keys enforcement for cascade integrity.
    - Write-Ahead Logging (WAL) for concurrent read/write throughput.
    - Busy timeout (10000ms) to prevent lock collisions under concurrent writes.
    - Synchronous=NORMAL for performance without compromising WAL reliability.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA busy_timeout=10000;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    # In-memory databases do not support WAL mode
    if ":memory:" not in str(settings.DATABASE_URL):
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
    cursor.close()


# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection providing transactional async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all database tables on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
