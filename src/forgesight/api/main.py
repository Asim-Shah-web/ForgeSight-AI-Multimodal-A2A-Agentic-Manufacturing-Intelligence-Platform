"""
FastAPI application entry point for ForgeSight AI.

Wires together lifespan startup/shutdown, all routers, global exception
handlers, CORS, and request-ID middleware.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from forgesight.config.database import create_db_and_tables, dispose_engine
from forgesight.config.logging import configure_logging, get_logger
from forgesight.config.redis_client import close_redis_pool, get_redis_client
from forgesight.config.settings import settings

# Import domain models so SQLModel.metadata is fully populated before
# create_db_and_tables() runs at startup.
import forgesight.domain.models  # noqa: F401

from forgesight.api.routes import auth as auth_routes
from forgesight.api.routes import health as health_routes
from forgesight.api.routes import incidents as incidents_routes
from forgesight.api.routes import users as users_routes

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    logger.info(
        "application_startup",
        extra={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug": settings.debug,
        },
    )

    await create_db_and_tables()

    redis_client = get_redis_client()
    try:
        await redis_client.ping()
        logger.info("redis_connection_warmed")
    finally:
        await redis_client.aclose()

    yield

    logger.info("application_shutdown_initiated")
    await dispose_engine()
    await close_redis_pool()
    logger.info("application_shutdown_complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Attach a unique X-Request-ID to every response for traceability."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return field-level validation errors as a structured 422 response."""
    logger.warning(
        "request_validation_error",
        extra={
            "path": str(request.url.path),
            "errors": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed.",
            "errors": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return a consistent JSON error body for all raised HTTPExceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled exceptions. Never leaks a stack trace to the
    client — logs the full exception server-side and returns only an
    incident reference the client can quote when reporting the issue.
    """
    incident_ref = str(uuid.uuid4())
    logger.exception(
        "unhandled_exception",
        extra={
            "path": str(request.url.path),
            "incident_ref": incident_ref,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred.",
            "incident_ref": incident_ref,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(incidents_routes.router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(users_routes.router, prefix="/api/v1/users", tags=["users"])
app.include_router(health_routes.router, prefix="/api/v1/health", tags=["health"])