"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.dependencies import get_plan_repository
from app.errors import register_error_handlers
from app.routers import admin, courses, suggest, upload

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    """Build the application, validating study plans eagerly so bad data fails at start-up."""
    settings = get_settings()
    get_plan_repository()

    app = FastAPI(title="Registration Assistant API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    for router in (courses.router, upload.router, suggest.router, admin.router):
        app.include_router(router, prefix="/api")

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, bool | str]:
        return {"status": "ok", "ai_enabled": settings.ai_enabled}

    return app


app = create_app()
