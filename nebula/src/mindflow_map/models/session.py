"""Database initialization and session management."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


def _is_sqlite_url(url: str) -> bool:
    return "sqlite" in url.lower()


def _run_alembic_migrations(database_url: str) -> None:
    """Run Alembic migrations synchronously using subprocess."""
    import subprocess
    import sys
    alembic_ini = os.path.join(os.path.dirname(__file__), "..", "..", "..", "alembic.ini")
    alembic_ini = os.path.abspath(alembic_ini)
    try:
        env = os.environ.copy()
        env["DATABASE_URL"] = database_url
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", alembic_ini, "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            cwd="/app",
        )
        logger.info("Alembic migrations completed: %s", result.stdout.strip())
    except subprocess.CalledProcessError as exc:
        logger.error("Alembic migration failed: %s", exc.stderr)
        raise RuntimeError(f"Database migration failed: {exc.stderr}") from exc


async def _create_all_tables(conn) -> None:
    """Create all tables via SQLAlchemy metadata (SQLite / test fallback)."""
    from mindflow_map.models.database import Base
    await conn.run_sync(Base.metadata.create_all)


class Database:
    """Database connection manager."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.async_session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._initialized = False
        self._use_alembic = not _is_sqlite_url(database_url)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        async with self.async_session_factory() as session:
            await self._ensure_initialized()
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def _ensure_initialized(self) -> None:
        """Initialize schema: Alembic for PostgreSQL, create_all for SQLite/tests."""
        if self._initialized:
            return
        if self._use_alembic:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: _run_alembic_migrations(self.database_url)
            )
        else:
            async with self.engine.begin() as conn:
                await _create_all_tables(conn)
        self._initialized = True

    async def init(self) -> None:
        """Initialize database schema."""
        if self._use_alembic:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: _run_alembic_migrations(self.database_url)
            )
        else:
            async with self.engine.begin() as conn:
                await _create_all_tables(conn)
        logger.info("Database initialized (%s)", "Alembic" if self._use_alembic else "create_all")

    async def close(self) -> None:
        """Close database engine."""
        await self.engine.dispose()


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database(settings.database_url)
    return _db


async def init_db() -> None:
    """Initialize database tables."""
    db = get_database()
    await db.init()
    logger.info("Database initialized")


async def close_db() -> None:
    """Close database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("Database connection closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting a database session."""
    db = get_database()
    async with db.get_session() as session:
        yield session
