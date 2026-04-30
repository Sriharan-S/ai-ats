from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import structured_error
from .runtime import ML_AVAILABLE

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aiats")


def create_app() -> FastAPI:
    app = FastAPI(title="AIATS API", version="2.0.0", docs_url=None, redoc_url=None)

    cors_raw = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")
    cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    from .routers import health, platforms, roadmaps
    app.include_router(health.router)
    app.include_router(roadmaps.router)
    app.include_router(platforms.router)

    if ML_AVAILABLE:
        from .routers import ats
        app.include_router(ats.router)
        logger.info("ML stack available — /api/ats-analyze enabled.")
    else:
        @app.post("/api/ats-analyze")
        def _ats_unsupported():
            return structured_error(
                "ATS_UNSUPPORTED_RUNTIME",
                "ATS analysis is unavailable on this runtime.",
                status=501,
            )
        logger.warning("ML stack unavailable — /api/ats-analyze returns 501.")

    from .routers import spa
    app.include_router(spa.router)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_request, exc: RequestValidationError):
        return structured_error(
            "VALIDATION_ERROR",
            "Request validation failed.",
            details={"errors": exc.errors()},
            status=400,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(_request, exc: StarletteHTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return structured_error(
                exc.detail["error"].get("code", "HTTP_ERROR"),
                exc.detail["error"].get("message", str(exc.detail)),
                details=exc.detail["error"].get("details"),
                status=exc.status_code,
            )
        return structured_error("HTTP_ERROR", str(exc.detail), status=exc.status_code)

    return app
