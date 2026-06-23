"""Run async SQLAlchemy services from synchronous Celery tasks."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    """Execute an async coroutine in a fresh event loop (Celery-safe)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def with_session(fn: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
    from app.db.database import init_db

    await init_db()
    from app.db.database import _session_factory

    async with _session_factory() as session:
        return await fn(session, *args, **kwargs)
