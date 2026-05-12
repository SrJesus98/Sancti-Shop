"""Database base and session management."""
from typing import AsyncGenerator, Generator

from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from app.core.config import settings


database_url = settings.DATABASE_URL
if database_url.startswith("sqlite+aiosqlite"):
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite", 1)

# Create engine with async support
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    poolclass=StaticPool if "sqlite" in database_url else None,
    echo=settings.DEBUG,
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session


# For async usage (future)
async def get_db() -> AsyncGenerator[Session, None]:
    """Async database session."""
    async with Session(engine) as session:
        yield session
