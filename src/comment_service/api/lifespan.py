from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from comment_service.core.config import Settings
from comment_service.core.db import init_engine, init_session_factory, close_engine
from comment_service.core.logging import get_logger

log = get_logger(__name__)


def build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("starting comment-service", extra={"env": settings.env})
        engine = await init_engine(settings.database_url, settings.sql_echo)
        session_factory = init_session_factory(engine)
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.settings = settings
        try:
            yield
        finally:
            log.info("stopping comment-service")
            await close_engine(engine)

    return lifespan

