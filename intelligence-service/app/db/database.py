from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.db.models import Base

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _ensure_data_dir() -> None:
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.split("///")[-1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"timeout": 30}
    return {}


async def init_db() -> None:
    global _engine, _session_factory
    _ensure_data_dir()
    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args=_sqlite_connect_args(settings.database_url),
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.database_url.startswith("sqlite"):
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            await conn.exec_driver_sql("PRAGMA busy_timeout=30000")
            await _migrate_unified_intel_columns(conn)
            await _migrate_intel_saint_columns(conn)


async def _migrate_intel_saint_columns(conn) -> None:
    """Add SAINT scoring columns on older intel SQLite tables (ALTER only, no data loss)."""
    saint_columns = (
        "risk_level VARCHAR(20) DEFAULT 'LOW'",
        "score_breakdown TEXT DEFAULT '{}'",
        "score_reason TEXT DEFAULT ''",
    )
    for table in (
        "intel_posts",
        "vendor_advisory_intel",
        "research_blog_intel",
        "vulnerability_intel",
    ):
        for col_def in saint_columns:
            try:
                await conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col_def}")
            except Exception:
                pass


async def _migrate_unified_intel_columns(conn) -> None:
    """Add unified_intel columns on existing SQLite DBs (create_all won't alter)."""
    new_columns = [
        "company_name VARCHAR(150)",
        "classification_confidence FLOAT DEFAULT 0.0",
        "classification_reason TEXT",
    ]
    for col_def in new_columns:
        col_name = col_def.split()[0]
        try:
            await conn.exec_driver_sql(f"ALTER TABLE unified_intel ADD COLUMN {col_def}")
        except Exception:
            pass  # column already exists


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        await init_db()
    async with _session_factory() as session:
        yield session
