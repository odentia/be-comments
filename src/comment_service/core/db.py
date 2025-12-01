from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from comment_service.core.logging import get_logger

log = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_engine(url: str, echo: bool = False) -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(url, echo=echo, pool_pre_ping=True)
        log.info("database engine initialized", extra={"url": url})
    return _engine


def init_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
        log.info("session factory ready")
    return _session_factory


async def close_engine(engine: AsyncEngine | None = None) -> None:
    global _engine, _session_factory
    target = engine or _engine
    if target is not None:
        await target.dispose()
        _engine = None
        _session_factory = None
        log.info("database engine closed")


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    return _session_factory

