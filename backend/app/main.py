from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import Settings
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as user_router


def create_app() -> FastAPI:
    settings = Settings()
    setup_logging(settings.log_level)

    app = FastAPI(title="FlowForge", version="0.1.0")
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    return app
