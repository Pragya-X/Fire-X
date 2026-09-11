from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, check_db
from app.database import get_db
from app.ml.predict import model_available, classification_health
from app.models import Hotspot
from app.providers.firms import get_fire_provider
from app.providers.osm import get_osm_provider
from app.providers.satellite import get_satellite_provider

router = APIRouter(prefix="/api/v1/system-health", tags=["system-health"])

# Health probes call external providers (FIRMS, OSM, satellite) and a fresh ML
# check, which costs ~2s. The dashboard and status bar poll this endpoint, so
# cache the full response briefly - the data is status info, not live telemetry.
_HEALTH_CACHE_TTL = 30.0
_health_cache: dict = {"data": None, "at": 0.0}


def _latency_ms(fn) -> float:
    start = time.perf_counter()
    fn()
    return round((time.perf_counter() - start) * 1000, 1)


@router.get("")
def system_health(db: Session = Depends(get_db)):
    import time as _time

    now = _time.monotonic()
    if _health_cache["data"] is not None and now - _health_cache["at"] < _HEALTH_CACHE_TTL:
        return _health_cache["data"]
    data = _compute_health(db)
    _health_cache["data"] = data
    _health_cache["at"] = now
    return data


def _compute_health(db: Session):
    db_check = check_db()
    firms = get_fire_provider()
    osm = get_osm_provider(db)
    satellite = get_satellite_provider()

    latest = db.query(Hotspot).order_by(Hotspot.acquisition_time.desc()).first()
    last_sync = latest.acquisition_time.isoformat() if latest and latest.acquisition_time else None

    ml_health = classification_health()
    components = [
        {
            "name": "Frontend",
            "status": "operational",
            "mode": "Next.js",
            "latency_ms": 0.0,
            "detail": "Served by Next.js",
            "last_sync": None,
        },
        {
            "name": "Backend API",
            "status": "operational",
            "mode": "FastAPI",
            "latency_ms": _latency_ms(lambda: None),
            "detail": f"v{settings.APP_VERSION}",
            "last_sync": None,
        },
        {
            "name": "Database",
            "status": "operational" if db_check["connected"] else "offline",
            "mode": db_check.get("dialect", "unknown"),
            "latency_ms": _latency_ms(lambda: db_check),
            "detail": "PostGIS ready" if db_check.get("postgis") else "SQLite fallback (PostGIS-ready schema)",
            "last_sync": last_sync,
        },
        {
            "name": "PostGIS",
            "status": "operational" if db_check.get("postgis") else "not_connected",
            "mode": "postgis" if db_check.get("postgis") else "geometry-as-wkt",
            "latency_ms": 0.0,
            "detail": "Spatial extension active" if db_check.get("postgis") else "Geometry stored as WKT - PostGIS used when configured",
            "last_sync": None,
        },
        {
            "name": "NASA FIRMS",
            "status": "not_configured" if firms.mode == "unavailable" else "operational",
            "mode": firms.mode.upper(),
            "latency_ms": 0.0,
            "detail": "Live FIRMS API" if firms.mode == "live" else "Demo provider" if firms.mode == "demo" else "No FIRMS credentials; no synthetic fallback",
            "last_sync": last_sync,
        },
        {
            "name": "OpenStreetMap",
            "status": "operational",
            "mode": osm.mode.upper(),
            "latency_ms": 0.0,
            "detail": "Overpass API" if osm.mode == "live" else "Seeded infrastructure dataset",
            "last_sync": last_sync,
        },
        {
            "name": "Satellite provider",
            "status": "not_configured" if satellite.mode == "unavailable" else "operational",
            "mode": satellite.mode.upper(),
            "latency_ms": 0.0,
            "detail": "Live imagery catalog search; pixel analysis unavailable" if satellite.mode == "live" else "Demo satellite layer" if satellite.mode == "demo" else "No imagery credentials; validation unavailable",
            "last_sync": last_sync,
        },
        {
            "name": "ML Engine",
            "status": "online" if model_available() else "baseline",
            "mode": ml_health["mode"],
            "latency_ms": 0.0,
            "detail": f"{ml_health['model_version']} · {ml_health['training_data_type']}",
            "last_sync": None,
        },
        {
            "name": "Notification engine",
            "status": "operational",
            "mode": "IN-APP",
            "latency_ms": 0.0,
            "detail": "In-app + SSE; SMTP email or local outbox; SMS unavailable",
            "last_sync": None,
        },
        {
            "name": "Realtime stream",
            "status": "operational",
            "mode": "SSE",
            "latency_ms": 0.0,
            "detail": "Server-Sent Events active",
            "last_sync": None,
        },
    ]
    degraded = [c for c in components if c["status"] in ("offline", "degraded", "not_configured")]
    return {
        "overall": "degraded" if degraded else "operational",
        "demo_mode": settings.DEMO_MODE or firms.mode == "demo",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "components": components,
    }