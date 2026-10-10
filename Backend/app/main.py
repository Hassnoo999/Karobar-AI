"""Karobaar AI backend entrypoint: FastAPI app, lifespan, CORS, and error mapping."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai.base import ProviderError
from app.auth import DEMO_MERCHANT
from app.config import settings
from app.data.seed import load_seed
from app.db import SessionLocal, engine, init_db
from app.errors import AIUnavailableError, DomainValidationError, KarobaarError, NotFoundError, StorageUnavailableError
from app.deployment import validate_deployment
from app.models import BusinessEvent
from app.routers import ALL_ROUTERS

logger = logging.getLogger(__name__)

# Serverless adapters do not all run ASGI lifespan. Validate at import too,
# before constructing an application that could serve unsafe default settings.
validate_deployment(settings)


async def _warmup_db_pool():
    """Background task: establish one warm connection in the pool at startup.

    Supabase Postgres in ap-northeast-1 (Tokyo) costs ~4s for the first SSL +
    PgBouncer handshake.  Warming the pool at startup means the first user
    request doesn't pay that penalty.
    """
    def _do_warmup():
        try:
            conn = engine.connect()
            conn.exec_driver_sql("SELECT 1")
            conn.close()
            logger.info("DB pool warmed (1 connection ready)")
        except Exception as exc:
            logger.warning("DB pool warmup skipped (%s)", type(exc).__name__)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _do_warmup)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_deployment(settings)
    if not settings.deployed:
        init_db()
    if settings.auto_seed:
        db = SessionLocal()
        try:
            if (
                db.query(BusinessEvent)
                .filter(BusinessEvent.merchant_id == DEMO_MERCHANT)
                .count() == 0
            ):
                load_seed(db, merchant_id=DEMO_MERCHANT)
        finally:
            db.close()
    # A reload/startup must not make a paid model call.
    warmup_db = asyncio.create_task(_warmup_db_pool())
    yield
    warmup_db.cancel()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Voice-first financial evidence and decision support for informal Pakistani "
        "merchants. AI captures and explains; deterministic SQL computes every number."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def private_api_headers(request: Request, call_next):
    # Vercel injects rotating OIDC request headers; the SDK reads a ContextVar.
    # Each request (including concurrent requests) has its own credential scope.
    from vercel.headers import set_headers
    set_headers(dict(request.headers) if settings.deployed else None)
    try:
        response = await call_next(request)
    finally:
        set_headers(None)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
    return response

for router in ALL_ROUTERS:
    app.include_router(router, prefix="/api")

def _error(status_code: int, error_type: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"type": error_type, "message": message}})


@app.exception_handler(NotFoundError)
async def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return _error(404, "not_found", str(exc))


@app.exception_handler(DomainValidationError)
async def _validation_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
    return _error(422, "validation_error", str(exc))


@app.exception_handler(AIUnavailableError)
async def _ai_unavailable_handler(request: Request, exc: AIUnavailableError) -> JSONResponse:
    # Upstream exceptions can contain request URLs, tokens or provider internals.
    return _error(503, "ai_unavailable", "AI recognition is temporarily unavailable. Retry or enter the facts manually.")


@app.exception_handler(ProviderError)
async def _provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
    return _error(503, "ai_unavailable", "AI recognition is temporarily unavailable. Retry or enter the facts manually.")


@app.exception_handler(StorageUnavailableError)
async def _storage_handler(request: Request, exc: StorageUnavailableError) -> JSONResponse:
    return _error(503, "storage_unavailable", str(exc))


@app.exception_handler(KarobaarError)
async def _karobaar_handler(request: Request, exc: KarobaarError) -> JSONResponse:
    return _error(400, "domain_error", str(exc))


@app.get("/", tags=["health"])
async def root():
    return {
        "name": settings.app_name,
        "environment": settings.environment,
        "docs": "/docs",
        "api_prefix": "/api",
    }
