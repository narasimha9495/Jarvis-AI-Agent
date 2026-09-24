"""Async SQLAlchemy database setup."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.config import get_settings
from app.db.models import Base

settings = get_settings()
db_url = settings.database_url if hasattr(settings, 'database_url') else "sqlite+aiosqlite:///./jarvis.db"

engine = create_async_engine(db_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    """Initialize database and create tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with async_session_maker() as session:
        yield session
