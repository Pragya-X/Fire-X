from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_role
from app.config import settings
from app.database import get_db
from app.models import ActivityLog, Alert, Hotspot, User
from app.providers.firms import DemoFireDataProvider, ProviderUnavailable, get_fire_provider
from app.providers.osm import SeededOsmProvider, get_osm_provider
from app.providers.satellite import get_satellite_provider
from app.seed_data import build_dataset
from app.services.classification_service import analyze_hotspot
from app.services.notification_service import notification_service
from app.services.sse import broadcast
from app.utils.helpers import Timer

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])
demo_router = APIRouter(prefix="/api/v1/ingest", tags=["demo"])

_dataset_cache: dict = {}


def get_dataset():
    key=(settings.DEMO_MODE,settings.REFERENCE_BUNDLE_PATH)
    if key not in _dataset_cache:
        if settings.REFERENCE_BUNDLE_PATH:
            from pathlib import Path
            from app.ml.reference_bundle import load_reference_bundle
            dataset,_=load_reference_bundle(Path(settings.REFERENCE_BUNDLE_PATH))
        elif settings.DEMO_MODE:
            dataset=build_dataset()
        else:
            from app.gis.engine import SpatialDataset
            dataset=SpatialDataset()  # Missing real references remain missing.
        _dataset_cache[key]=dataset
    return _dataset_cache[key]


def _upsert_detections(db: Session, records: list[dict], source_tag: str) -> dict:
    created = 0
    updated = 0
    alerts_before = db.query(Alert).count()
    max_id = db.query(Hotspot).count() + 1

    for rec in records:
        lat, lon = float(rec["latitude"]), float(rec["longitude"])
        acq = datetime.fromisoformat(rec.get("acq_time") or datetime.now(timezone.utc).isoformat())
        # dedupe by external_id
        existing = None
        if rec.get("external_id"):
            existing = db.query(Hotspot).filter(Hotspot.external_id == rec["external_id"]).first()
        if existing:
            updated += 1
            existing.brightness = float(rec.get("brightness", existing.brightness))
            existing.frp = float(rec.get("frp", existing.frp))
            continue

        hs = Hotspot(
            code=f"HX-{max_id:04d}",
            external_id=rec.get("external_id"),
            latitude=lat, longitude=lon,
            geometry=f"POINT({lon} {lat})",
            acquisition_time=acq,
            brightness=float(rec.get("brightness", 300)),
            frp=float(rec.get("frp", 1)),
            confidence=float(rec.get("confidence", 0.8)),
            source=rec.get("source", source_tag),
            satellite=rec.get("satellite", "VIIRS S-NPP"),
            daynight=rec.get("daynight", "D"),
        )
        db.add(hs)
        db.flush()
        max_id += 1
        from app.gis.engine import compute_infrastructure_features
        from app.models import InfrastructureFeature

        ctx = compute_infrastructure_features(get_dataset(), lat, lon)
        ftr = InfrastructureFeature(hotspot_id=hs.id, **ctx)
        db.add(ftr)
        db.flush()  # ensure the lazy-loaded relationship sees the row
        hs.land_cover = get_dataset().land_cover(lat, lon)
        analyze_hotspot(db, hs, get_dataset())
        created += 1

    db.commit()
    # Auto-alerts for high-risk / high-confidence industrial fires
    alerts_created = 0
    new_hotspots = db.query(Hotspot).filter(Hotspot.source == source_tag).order_by(Hotspot.id.desc()).limit(max(created, 1)).all()
    for hs in new_hotspots[:30]:
        if hs.risk_score >= settings.AUTO_ALERT_RISK_THRESHOLD or (
            hs.classification in ("Industrial Fire", "Gas Flare") and hs.classification_confidence >= 0.8
        ):
            alert = Alert(
                code=f"AL-{db.query(Alert).count() + 1:04d}",
                hotspot_id=hs.id,
                alert_type="industrial_fire" if hs.classification == "Industrial Fire" else "risk",
                severity=hs.risk_level if hs.risk_level in ("CRITICAL", "HIGH") else "MODERATE",
                title=f"Auto-alert: {hs.classification} near {hs.district or hs.state}",
                message=f"{hs.code} risk {hs.risk_score:.0f}/100 - {hs.classification} with {hs.classification_confidence*100:.0f}% confidence.",
                location=f"{hs.district}, {hs.state}",
                confidence=round(hs.classification_confidence, 2),
                risk_score=hs.risk_score,
                status="new",
                recommended_action="Immediate field verification recommended." if hs.risk_level == "CRITICAL" else "Priority inspection recommended.",
            )
            db.add(alert)
            db.flush()  # keep Alert.count() accurate for the next iteration
            alerts_created += 1
    db.commit()
    broadcast({"type": "ingest", "data": {"created": created, "updated": updated, "alerts": alerts_created}})
    return {"created": created, "updated": updated, "alerts_created": alerts_created}


@router.post("/firms", response_model=dict)
def ingest_firms(user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    timer = Timer()
    provider = get_fire_provider()
    errors: list[str] = []
    try:
        records = provider.fetch()
    except ProviderUnavailable as exc:
        if not settings.DEMO_MODE:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        errors.append(str(exc))
        provider = DemoFireDataProvider()
        records = provider.fetch()
    result = _upsert_detections(db, records, provider.mode)
    db.add(ActivityLog(user=user.email, action="data_ingestion", entity="firms", details={"mode": provider.mode, **result}))
    db.commit()
    notification_service.notify(
        db, title="FIRMS sync complete",
        message=f"Synced {result['created']} new detections ({provider.mode.upper()} MODE).",
        severity="info", entity="ingest",
        user_id=user.id, to=user.email,
        channels=["in-app", "email"],
    )
    return {"provider": provider.name, "mode": provider.mode, "validation_report": getattr(provider, "validation_report", None), "records_received": len(records), **result, "duration_ms": timer.elapsed_ms(), "errors": errors}


@demo_router.post("/demo", response_model=dict)
def ingest_demo(user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    timer = Timer()
    provider = DemoFireDataProvider()
    records = provider.fetch()
    result = _upsert_detections(db, records, "demo")
    db.add(ActivityLog(user=user.email, action="data_ingestion", entity="demo", details=result))
    notification_service.notify(
        db, title="Sample detection batch ingested",
        message=f"{result['created']} new detection(s) ingested and analyzed.",
        severity="info", entity="ingest",
        user_id=user.id, to=user.email,
        channels=["in-app", "email"],
    )
    db.commit()
    return {"provider": provider.name, "mode": "demo", "records_received": len(records), **result, "duration_ms": timer.elapsed_ms(), "errors": []}


@router.post("/osm", response_model=dict)
def ingest_osm(user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    timer = Timer()
    provider = get_osm_provider(db)
    items = provider.fetch(db) if isinstance(provider, SeededOsmProvider) else provider.fetch()
    db.add(ActivityLog(user=user.email, action="data_ingestion", entity="osm", details={"mode": provider.mode, "count": len(items)}))
    db.commit()
    return {"provider": provider.name, "mode": provider.mode, "records": len(items), "duration_ms": timer.elapsed_ms(), "errors": []}


@demo_router.post("/landcover", response_model=dict)
def ingest_landcover(user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    from app.providers.landcover import SeededLandCoverProvider

    timer = Timer()
    provider = SeededLandCoverProvider()
    data = provider.fetch()
    db.add(ActivityLog(user=user.email, action="data_ingestion", entity="landcover", details={"mode": provider.mode, "features": len(data.get("features", []))}))
    db.commit()
    return {"provider": provider.name, "mode": provider.mode, "features": len(data.get("features", [])), "duration_ms": timer.elapsed_ms(), "errors": []}


@router.post("/refresh-analysis", response_model=dict)
def refresh_analysis(user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    timer = Timer()
    from app.services.classification_service import refresh_all

    result = refresh_all(db, get_dataset())
    db.add(ActivityLog(user=user.email, action="classification", entity="hotspot", details={"refreshed": result["updated"]}))
    db.commit()
    return {"updated": result["updated"], "duration_ms": timer.elapsed_ms()}


@router.post("/run-classification", response_model=dict)
def run_classification(body: Optional[dict] = None, user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    timer = Timer()
    hs_id = (body or {}).get("hotspot_id")
    if hs_id:
        h = db.get(Hotspot, int(hs_id))
        if h is None:
            return {"error": "hotspot not found", "duration_ms": timer.elapsed_ms()}
        res = analyze_hotspot(db, h, get_dataset())
        db.add(ActivityLog(user=user.email, action="classification", entity="hotspot", entity_id=h.code))
        db.commit()
        return {"classification": res["classification"], "confidence": res["confidence"], "risk_score": res["risk"]["score"], "duration_ms": timer.elapsed_ms()}
    return refresh_analysis(user=user, db=db)


@router.post("/recalculate-risk", response_model=dict)
def recalculate_risk(user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    timer = Timer()
    from app.services.classification_service import refresh_all

    result = refresh_all(db, get_dataset())
    db.add(ActivityLog(user=user.email, action="risk_update", entity="hotspot", details={"updated": result["updated"]}))
    db.commit()
    return {"updated": result["updated"], "duration_ms": timer.elapsed_ms()}


@router.post("/satellite/validate", response_model=dict)
def validate_satellite(body: dict, user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    from app.models import SatelliteValidation

    timer = Timer()
    hs = db.get(Hotspot, int(body.get("hotspot_id", 0)))
    if hs is None:
        return {"error": "hotspot not found", "duration_ms": timer.elapsed_ms()}
    provider = get_satellite_provider()
    result = provider.validate(hs)
    db.add(SatelliteValidation(hotspot_id=hs.id, **result, validated_at=datetime.now(timezone.utc)))
    db.add(ActivityLog(user=user.email, action="satellite_validation", entity="hotspot", entity_id=hs.code, details={"status": result["status"]}))
    db.commit()
    # Re-run analysis so satellite score influences classification + risk
    analyze_hotspot(db, hs, get_dataset())
    db.commit()
    broadcast({"type": "satellite_validation", "data": {"hotspot": hs.code, "status": result["status"]}})
    return {**result, "provider": provider.mode, "duration_ms": timer.elapsed_ms()}
