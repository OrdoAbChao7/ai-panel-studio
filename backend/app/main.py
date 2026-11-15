"""AI Panel Studio — Backend Application Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.infrastructure.database import init_db
from app.infrastructure.session_manager import session_manager
from app.interfaces.api_router import router as api_router
from app.interfaces.sse_router import router as sse_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle manager."""
    # Startup: Initialize SQLite database schema
    await init_db()
    yield
    # Shutdown: Clean up background session tasks
    await session_manager.shutdown_all()


app = FastAPI(
    title="AI Panel Studio API",
    version="0.1.0",
    description="Backend service for Autonomous Multi-Agent Round-Table Debate Platform",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(api_router)
app.include_router(sse_router)


@app.get("/api/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """Service health verification endpoint."""
    return JSONResponse(
        content={
            "status": "ok",
            "app": "AI Panel Studio",
            "version": "0.1.0",
        }
    )
