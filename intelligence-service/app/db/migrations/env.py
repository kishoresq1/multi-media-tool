import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if service_root not in sys.path:
    sys.path.insert(0, service_root)

try:
    from app.db.base import Base  # type: ignore

    # Import all ORM models so that Base.metadata is populated before any
    # autogenerate or upgrade run.  The flat models.py is the authoritative
    # source; the per-file models/ sub-package is kept for compatibility.
    import app.db.models  # noqa: F401  — registers all table metadata
except ModuleNotFoundError:
    target_metadata = None
else:
    target_metadata = Base.metadata


def get_database_url() -> str:
    """Return an asyncpg URL from DATABASE_URL or alembic.ini."""
    database_url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to run Alembic migrations")
    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        database_url = database_url.replace("://", "+asyncpg://", 1)
    return database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()
    connectable = async_engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
