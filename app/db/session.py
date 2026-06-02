"""Database base and session management."""
from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine as sync_create_engine
from sqlalchemy.orm import Session as SyncSession, sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from app.core.config import settings


database_url = settings.DATABASE_URL  # ej: sqlite+aiosqlite:///./ecommerce.db

# ─── 1) ASYNC ENGINE (para API endpoints) ────────────────
async_engine = create_async_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async DB session for API endpoints."""
    async with AsyncSessionLocal() as session:
        yield session


# ─── 2) SYNC ENGINE (para startup, seed, y vistas) ──────
_sync_url = database_url.replace("sqlite+aiosqlite", "sqlite", 1)
sync_engine = sync_create_engine(
    _sync_url,
    connect_args={"check_same_thread": False} if "sqlite" in _sync_url else {},
    echo=settings.DEBUG,
)

SyncSessionLocal = sessionmaker(sync_engine, class_=SyncSession)


def get_session() -> Generator[SyncSession, None, None]:
    """Get sync DB session (for views and startup)."""
    with SyncSessionLocal() as session:
        yield session


# ─── 3) CREATE TABLES (async) ───────────────────────────
async def create_db_and_tables():
    """Create all database tables using async engine."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# ─── 4) LEGACY — mantener por compatibilidad ────────────
def create_db_and_tables_sync():
    """Sync version for startup (llamado desde lifespan)."""
    SQLModel.metadata.create_all(sync_engine)
