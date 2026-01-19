import uvicorn

from comment_service.api.app import create_app
from comment_service.core.config import load_settings


def main():
    settings = load_settings()
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.http_host,
        port=settings.http_port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()
