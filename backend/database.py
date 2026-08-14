import os
import logging
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.config import settings

logger = logging.getLogger(__name__)

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Ensure directory exists for SQLite database
if is_sqlite:
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if "/" in db_path:
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

# Derive Asynchronous Database URL
if settings.DATABASE_URL.startswith("sqlite:///"):
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif settings.DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif settings.DATABASE_URL.startswith("postgres://"):
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
elif "asyncpg" in settings.DATABASE_URL or "aiosqlite" in settings.DATABASE_URL:
    ASYNC_DATABASE_URL = settings.DATABASE_URL
else:
    ASYNC_DATABASE_URL = settings.DATABASE_URL

# Synchronous Engine & Session (For Celery tasks and migration scripts)
sync_connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=sync_connect_args,
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous Engine & Session with Connection Pooling (For FastAPI async routes)
async_connect_args = {"check_same_thread": False} if is_sqlite else {}
async_pool_kwargs = {}
if not is_sqlite:
    async_pool_kwargs = {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args=async_connect_args,
    echo=False,
    pool_pre_ping=True,
    **async_pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an asynchronous database session from the connection pool."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
