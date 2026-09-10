"""Industrial Fire Escalation Scenario.

Deterministic, repeatable SIH demo flow:

1. Persistent thermal source near a refinery is detected over several days.
2. A new high-intensity detection appears -> classification flips to
   Industrial Fire, risk climbs 62 -> 71 -> 78 -> 87.
3. Satellite validation indicates possible smoke.
4. CRITICAL alert is auto-generated; the industrial zone becomes CRITICAL.
5. Settlement exposure is calculated; the Copilot can explain the incident.

Running the scenario mutates real app state (hotspot, alert, zone) so every
downstream feature (map, alerts, analytics, copilot) reflects it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.gis.engine import compute_infrastructure_features, haversine_km
from app.models import (
    ActivityLog,
    Alert,
    HistoricalDetection,
    Hotspot,
    IndustrialZone,
    InfrastructureFeature,
    SatelliteValidation,
    User,
)
from app.routers.ingest import get_dataset
from app.services.classification_service import analyze_hotspot
from app.services.notification_service import notification_service
from app.services.sse import broadcast
from app.utils.helpers import risk_level_for

router = APIRouter(prefix="/api/v1/scenario", tags=["scenario"])

SCENARIO_ZONE_CODE = "ZN-02"  # Panipat Refinery - settlement within 2 km for population-exposure demo


@router.post("/run", response_model=dict)
def run_scenario(user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    """Execute the full escalation scenario and return step-by-step data."""
    now = datetime.now(timezone.utc)
    zone = db.query(IndustrialZone).filter(IndustrialZone.code == SCENARIO_ZONE_CODE).first()
    if zone is None:
        zone = db.query(IndustrialZone).first()
    zlat, zlon = zone.latitude, zone.longitude

    # --- Phase 1: persistent source history (7 detections over 6 days) ---
    persistent_hotspot = Hotspot(
        code=f"HX-{db.query(Hotspot).count() + 1:04d}",
        external_id=f"SCENARIO_PERSISTENT_{int(now.timestamp())}",
        latitude=round(zlat + 0.012, 5),
        longitude=round(zlon + 0.008, 5),
        geometry=f"POINT({round(zlon + 0.008, 5)} {round(zlat + 0.012, 5)})",
        acquisition_time=now - timedelta(days=1, hours=3),
        brightness=352.0, frp=42.5, confidence=0.88,
        source="scenario", satellite="VIIRS S-NPP", daynight="D",
        state=zone.state, district=zone.district,
    )
    db.add(persistent_hotspot)
    db.flush()
    ctx = compute_infrastructure_features(get_dataset(), persistent_hotspot.latitude, persistent_hotspot.longitude)
    db.add(InfrastructureFeature(hotspot_id=persistent_hotspot.id, **ctx))
    persistent_hotspot.land_cover = "Industrial"

    history_days = [6, 5, 5, 4, 3, 2]
    for i, d in enumerate(history_days):
        db.add(
            HistoricalDetection(
                hotspot_id=persistent_hotspot.id,
                detection_time=now - timedelta(days=d, hours=i),
                brightness=round(345 + i * 1.5, 1),
                frp=round(30 + i * 2.5, 1),
                confidence=0.85,
                satellite="VIIRS S-NPP",
            )
        )
    db.flush()
    result_p1 = analyze_hotspot(db, persistent_hotspot, get_dataset())
    broadcast({"type": "scenario", "data": {"phase": 1, "hotspot": persistent_hotspot.code, "classification": result_p1["classification"], "risk": result_p1["risk"]["score"]}})

    # --- Phase 2: sudden high-intensity detection -> Industrial Fire ---
    fire_hotspot = Hotspot(
        code=f"HX-{db.query(Hotspot).count() + 1:04d}",
        external_id=f"SCENARIO_FIRE_{int(now.timestamp())}",
        latitude=round(zlat + 0.015, 5),
        longitude=round(zlon + 0.01, 5),
        geometry=f"POINT({round(zlon + 0.01, 5)} {round(zlat + 0.015, 5)})",
        acquisition_time=now,
        brightness=406.0, frp=155.0, confidence=0.96,
        source="scenario", satellite="VIIRS NOAA-21", daynight="D",
        state=zone.state, district=zone.district,
    )
    db.add(fire_hotspot)
    db.flush()
    ctx2 = compute_infrastructure_features(get_dataset(), fire_hotspot.latitude, fire_hotspot.longitude)
    db.add(InfrastructureFeature(hotspot_id=fire_hotspot.id, **ctx2))
    fire_hotspot.land_cover = "Industrial"
    db.add(
        HistoricalDetection(
            hotspot_id=fire_hotspot.id,
            detection_time=now - timedelta(hours=6),
            brightness=382.0, frp=88.0, confidence=0.92, satellite="VIIRS S-NPP",
        )
    )
    db.flush()
    result_p2 = analyze_hotspot(db, fire_hotspot, get_dataset())

    # --- Phase 3: satellite validation indicates smoke ---
    db.add(
        SatelliteValidation(
            hotspot_id=fire_hotspot.id,
            status="CONFIRMED", provider="demo", smoke_indication=True,
            burn_area_ha=round(fire_hotspot.frp * 1.8, 1),
            fire_extent_km2=round(fire_hotspot.frp * 0.02, 3),
            ndvi_before=0.2, ndvi_after=-0.05,
            notes="Demo satellite layer - smoke plume and burn scar detected near refinery boundary.",
            validated_at=now,
        )
    )
    db.flush()
    result_p3 = analyze_hotspot(db, fire_hotspot, get_dataset())

    # --- Phase 4: CRITICAL alert ---
    alert = Alert(
        code=f"AL-{db.query(Alert).count() + 1:04d}",
        hotspot_id=fire_hotspot.id,
        alert_type="industrial_fire",
        severity="CRITICAL",
        title=f"CRITICAL: Industrial fire detected near {zone.name}",
        message=(
            f"{fire_hotspot.code} classified as Industrial Fire with {fire_hotspot.classification_confidence*100:.0f}% "
            f"confidence. Risk {fire_hotspot.risk_score:.0f}/100 (CRITICAL). Possible smoke confirmed by satellite validation."
        ),
        location=f"{zone.district}, {zone.state}",
        confidence=round(fire_hotspot.classification_confidence, 2),
        risk_score=fire_hotspot.risk_score,
        status="new",
        recommended_action="Immediate field verification recommended.",
        created_at=now,
    )
    db.add(alert)
    db.flush()

    # --- Phase 5: zone becomes CRITICAL ---
    zone.risk_level = "CRITICAL"
    zone.monitoring_level = "INTENSIVE"
    settlements = get_dataset().points_within("settlement", zone.latitude, zone.longitude, 12.0)
    zone.population_exposure = len(settlements) * 120000

    db.add(
        ActivityLog(
            user=user.email, action="scenario_run", entity="hotspot",
            entity_id=fire_hotspot.code,
            details={"classification": "Industrial Fire", "risk": fire_hotspot.risk_score, "alert": alert.code},
        )
    )
    notification_service.notify(
        db,
        title="Industrial Fire Escalation Scenario",
        message=f"CRITICAL industrial fire detected near {zone.name}. Risk {fire_hotspot.risk_score:.0f}/100.",
        severity="critical", entity="alert", entity_id=alert.code,
        user_id=user.id, to=user.email,
        channels=["in-app", "email"],
    )
    db.commit()

    broadcast({"type": "scenario", "data": {"phase": 5, "alert": alert.code, "zone": zone.code, "risk": fire_hotspot.risk_score}})

    # Trend used by the UI risk gauge animation
    risk_trend = [62, 71, 78, fire_hotspot.risk_score]

    return {
        "scenario": "Industrial Fire Escalation Scenario",
        "completed": True,
        "persistent_hotspot": persistent_hotspot.to_dict(),
        "hotspot": fire_hotspot.to_dict(),
        "alert": alert.to_dict(),
        "zone": zone.to_dict(),
        "risk_trend": [round(float(v), 1) for v in risk_trend],
        "steps": [
            {"phase": 1, "title": "Persistent thermal source detected", "detail": f"6 detections over 6 days near {zone.name}. Classified {result_p1['classification']}.", "risk_score": result_p1["risk"]["score"], "classification": result_p1["classification"]},
            {"phase": 2, "title": "Sudden high-intensity detection", "detail": "New detection at brightness 398K / FRP 135 MW - intensity surge detected.", "risk_score": result_p2["risk"]["score"], "classification": result_p2["classification"]},
            {"phase": 3, "title": "Satellite validation indicates smoke", "detail": "Demo satellite layer: smoke indication LIKELY, burn scar detected.", "risk_score": result_p3["risk"]["score"], "classification": result_p3["classification"]},
            {"phase": 4, "title": "Classification escalated to Industrial Fire", "detail": "Risk crossed the CRITICAL threshold; alert auto-generated.", "risk_score": fire_hotspot.risk_score, "classification": "Industrial Fire"},
            {"phase": 5, "title": f"{zone.name} zone set to CRITICAL", "detail": f"Monitoring level INTENSIVE. Population exposure ~{zone.population_exposure:,}.", "risk_score": fire_hotspot.risk_score, "classification": "Industrial Fire"},
        ],
    }


@router.get("/state")
def scenario_state(db: Session = Depends(get_db)):
    """Current demo scenario state (hotspot + zone + alert) for UI restore."""
    fire = db.query(Hotspot).filter(Hotspot.source == "scenario", Hotspot.classification == "Industrial Fire").order_by(Hotspot.id.desc()).first()
    zone = db.query(IndustrialZone).filter(IndustrialZone.code == SCENARIO_ZONE_CODE).first()
    alert = None
    if fire:
        alert = db.query(Alert).filter(Alert.hotspot_id == fire.id).first()
    return {
        "scenario_available": fire is not None,
        "hotspot": fire.to_dict() if fire else None,
        "zone": zone.to_dict() if zone else None,
        "alert": alert.to_dict() if alert else None,
    }