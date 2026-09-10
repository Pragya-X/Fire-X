"""FIRE-X - Fire Intelligence & Risk Evaluation Platform - FastAPI backend."""
from __future__ import annotations

import logging
import time
import uuid
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import SessionLocal, init_db
from app.routers import (
    thermal_events,
    alerts,
    analytics,
    auth,
    copilot,
    events,
    hotspots,
    context,
    ingest,
    ml,
    reports,
    scenario,
    system,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("firex")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FIRE-X backend starting...")
    init_db()
    # Ensure demo users exist on first boot (idempotent)
    try:
        from app.models import User

        db = SessionLocal()
        if settings.DEMO_MODE and settings.ENV != "production" and db.query(User).count() == 0:
            from app.seed import main as seed_main

            seed_main()
        db.close()
    except Exception as exc:  # pragma: no cover
        logger.warning("Auto-seed skipped: %s", exc)
    yield
    logger.info("FIRE-X backend stopped")


app = FastAPI(
    title="FIRE-X API",
    description="Fire Intelligence & Risk Evaluation Platform - AI-enabled geospatial fire intelligence.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False if "*" in settings.cors_origin_list else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in [
    auth.router,
    hotspots.router,
    context.router,
    alerts.router,
    analytics.router,
    ml.router,
    ingest.router,
    reports.router,
    system.router,
    events.router,
    copilot.router,
    thermal_events.router,
]:
    app.include_router(r)

if settings.DEMO_MODE and settings.ENV != "production":
    app.include_router(ingest.demo_router)
    app.include_router(scenario.router)

# Local file storage for uploads (dev)
app.mount("/storage", StaticFiles(directory=settings.UPLOAD_DIR), name="storage")


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs", "health": "/api/v1/system-health"}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}

@app.middleware("http")
async def request_logging(request, call_next):
    request_id = uuid.uuid4().hex
    started = time.monotonic()
    demo_path = request.url.path.startswith("/api/v1/scenario") or request.url.path in {
        "/api/v1/ingest/demo", "/api/v1/ingest/landcover",
    }
    if demo_path and (not settings.DEMO_MODE or settings.ENV == "production"):
        response = JSONResponse({"detail": "Demonstration endpoints are disabled"}, status_code=404)
    else:
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    # Never log query strings, credentials, annotation evidence or request bodies.
    logger.info("request_id=%s method=%s status=%s elapsed_ms=%.1f", request_id,
                request.method, response.status_code, (time.monotonic()-started)*1000)
    return response
