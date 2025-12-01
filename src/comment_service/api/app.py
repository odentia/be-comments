from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from comment_service.api.lifespan import build_lifespan
from comment_service.api.v1.routers import api_v1
from comment_service.core.config import Settings, load_settings
from comment_service.core.logging import init_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    init_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
        lifespan=build_lifespan(settings),
    )

    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1, prefix="/api")
    app.state.settings = settings
    return app

