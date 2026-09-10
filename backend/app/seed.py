"""Seed the FIRE-X database with realistic India-focused demo data.

Run from the backend directory:

    python -m app.seed

Wipes existing demo rows and recreates everything deterministically (seed 42).
Writes ``data/network.geojson`` and ``data/landcover.geojson`` used by the
GIS API layers.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete

from app.auth import hash_password
from app.config import settings
from app.database import SessionLocal, init_db
from app.gis.engine import compute_infrastructure_features
from app.models import (
    ActivityLog,
    Alert,
    HistoricalDetection,
    Hotspot,
    IndustrialZone,
    Infrastructure,
    InfrastructureFeature,
    Notification,
    SatelliteValidation,
    User,
)
from app.seed_data import (
    CITIES,
    FACTORIES,
    FORESTS,
    INDUSTRIAL_ZONES,
    MINES,
    POWER_PLANTS,
    REFINERIES,
    STATES,
    build_dataset,
    generate_hotspot_specs,
)
from app.services.classification_service import analyze_hotspot
from app.services.notification_service import notification_service
from app.utils.helpers import risk_level_for

SEED_USERS = [
    ("npgearly@gmail.com", "NPG Early", "admin"),
]
SEED_PASSWORD = "admin123"


def _district_for_zone(zone) -> str:
    return zone[6]


def wipe(db) -> None:
    for model in [SatelliteValidation, Alert, Notification, ActivityLog, InfrastructureFeature, HistoricalDetection, Hotspot, Infrastructure, IndustrialZone, User]:
        db.execute(delete(model))
    db.commit()


def seed_users(db) -> list[User]:
    users = []
    for email, name, role in SEED_USERS:
        u = User(email=email, name=name, role=role, password_hash=hash_password(SEED_PASSWORD))
        db.add(u)
        users.append(u)
    db.commit()
    for u in users:
        db.refresh(u)
    return users


def seed_zones(db) -> list[IndustrialZone]:
    zones = []
    for code, name, ztype, lat, lon, state, district in INDUSTRIAL_ZONES:
        z = IndustrialZone(
            code=code, name=name, zone_type=ztype, latitude=lat, longitude=lon,
            state=state, district=district, radius_km=6.0,
            risk_level="LOW", monitoring_level="ROUTINE",
            description=f"{ztype} monitoring zone at {name}, {district}, {state}.",
        )
        db.add(z)
        zones.append(z)
    db.commit()
    for z in zones:
        db.refresh(z)
    return zones


def seed_infrastructure(db, dataset, zones_by_code) -> None:
    idx = 0

    def add(name, itype, lat, lon, state, district, zone=None):
        nonlocal idx
        idx += 1
        code = f"IF-{idx:03d}"
        db.add(Infrastructure(code=code, name=name, infra_type=itype, latitude=lat, longitude=lon,
                              state=state, district=district, zone_id=zone.id if zone else None))

    for zone in INDUSTRIAL_ZONES:
        code, name, ztype, lat, lon, state, district = zone
        zobj = zones_by_code.get(code)
        mapped = {"Refinery": "refinery", "Factory": "factory", "Power Plant": "power_plant", "Mine": "mine"}.get(ztype)
        if mapped:
            add(name, mapped, lat, lon, state, district, zobj)
    for r in REFINERIES:
        add(r[1], "refinery", r[2], r[3], r[4], r[5])
    for f in FACTORIES:
        add(f[1], "factory", f[2], f[3], f[4], f[5])
    for p in POWER_PLANTS:
        add(p[1], "power_plant", p[2], p[3], p[4], p[5])
    for m in MINES:
        add(m[1], "mine", m[2], m[3], m[4], m[5])
    for c in CITIES:
        add(c[0], "settlement", c[2], c[3], c[1], "")
    db.commit()


def seed_hotspots(db, dataset, now) -> int:
    rng = random.Random(42)
    specs = generate_hotspot_specs(320, rng=rng, now=now)
    hotspots: list[Hotspot] = []

    for spec in specs:
        hs = Hotspot(
            code=f"HX-{spec['i'] + 1:04d}",
            external_id=f"VNP14IMGTDL_NRT_{90000000 + spec['i'] * 173}",
            latitude=spec["lat"], longitude=spec["lon"],
            geometry=f"POINT({spec['lon']} {spec['lat']})",
            acquisition_time=spec["acquisition"],
            brightness=spec["brightness"], frp=spec["frp"], confidence=spec["confidence"],
            source="demo", satellite=spec["satellite"], daynight=spec["daynight"],
            state=spec["state"], district=spec["district"],
        )
        db.add(hs)
        db.flush()

        # Infrastructure features
        ctx = compute_infrastructure_features(dataset, spec["lat"], spec["lon"])
        db.add(InfrastructureFeature(hotspot_id=hs.id, **ctx))

        # Land cover from spatial context
        hs.land_cover = dataset.land_cover(spec["lat"], spec["lon"], rng)

        # Historical detections (thermal params drift around the current values)
        for ht in _detection_times(spec["pattern"], spec["acquisition"], rng):
            db.add(HistoricalDetection(
                hotspot_id=hs.id, detection_time=ht,
                brightness=round(spec["brightness"] * rng.uniform(0.94, 1.06), 1),
                frp=round(max(0.5, spec["frp"] * rng.uniform(0.85, 1.15)), 2),
                confidence=round(rng.uniform(0.6, 1.0), 2), satellite=hs.satellite,
            ))
        db.flush()
        hotspots.append(hs)

    db.commit()

    # Classification + risk pass (also sets persistence / explanation)
    analyzed = 0
    for hs in hotspots:
        analyze_hotspot(db, hs, dataset)
        analyzed += 1
    db.commit()

    # Satellite validations for a subset
    v_rng = random.Random(99)
    validated = [h for h in hotspots if v_rng.random() < 0.16]
    for hs in validated:
        status = _validation_status_for(hs, v_rng)
        smoke = hs.classification in ("Wildfire", "Industrial Fire") and v_rng.random() < 0.7
        ndvi_before = _ndvi_for(hs.land_cover, v_rng)
        ndvi_after = max(-0.2, round(ndvi_before - v_rng.uniform(0.05, 0.35), 3))
        db.add(SatelliteValidation(
            hotspot_id=hs.id, status=status, provider="demo",
            smoke_indication=smoke,
            burn_area_ha=round(max(0.5, hs.frp * v_rng.uniform(1.0, 2.2)), 1),
            fire_extent_km2=round(max(0.01, hs.frp * 0.02), 3),
            ndvi_before=ndvi_before, ndvi_after=ndvi_after,
            notes=f"Demo satellite layer - vegetation change detected ({status.lower()}).",
        ))
    db.commit()

    # Alerts
    seed_alerts(db, hotspots)
    return len(hotspots)


def _detection_times(pattern: str, acquisition: datetime, rng: random.Random):
    from app.seed_data import _history_for_pattern as _hfp

    return _hfp(pattern, acquisition, rng)


def _validation_status_for(hs: Hotspot, rng: random.Random) -> str:
    table = {
        "Wildfire": ["CONFIRMED", "LIKELY", "LIKELY", "UNCERTAIN"],
        "Industrial Fire": ["CONFIRMED", "LIKELY", "LIKELY", "UNCERTAIN"],
        "Persistent Industrial Heat Source": ["LIKELY", "UNCERTAIN", "UNCERTAIN"],
        "Gas Flare": ["LIKELY", "UNCERTAIN"],
        "Agricultural Burning": ["LIKELY", "LIKELY", "UNCERTAIN"],
        "Other Thermal Anomaly": ["UNCERTAIN", "NOT VALIDATED", "UNCERTAIN"],
    }
    return rng.choice(table.get(hs.classification, ["UNCERTAIN"]))


def _ndvi_for(land_cover: str, rng: random.Random) -> float:
    base = {"Forest": 0.5, "Agriculture": 0.4, "Industrial": 0.18, "Urban": 0.15, "Barren": 0.12, "Other": 0.2}
    return round(max(0.0, base.get(land_cover, 0.2) + rng.uniform(-0.05, 0.06)), 3)


def seed_alerts(db, hotspots) -> None:
    rng = random.Random(7)
    officers = ["NPG Early"]
    statuses = ["new", "new", "new", "acknowledged", "acknowledged", "investigating", "investigating", "escalated", "resolved", "resolved"]

    alert_idx = 0
    candidates = [
        h for h in hotspots
        if h.risk_score >= 75 or (h.classification in ("Industrial Fire", "Gas Flare") and h.classification_confidence >= 0.7)
    ]
    rng.shuffle(candidates)
    for hs in candidates[:32]:
        alert_idx += 1
        severity = hs.risk_level if hs.risk_level in ("CRITICAL", "HIGH", "ELEVATED") else "MODERATE"
        status = rng.choice(statuses)
        title = _alert_title(hs)
        message = _alert_message(hs)
        db.add(Alert(
            code=f"AL-{alert_idx:04d}",
            hotspot_id=hs.id,
            alert_type=_alert_type(hs),
            severity=severity,
            title=title,
            message=message,
            location=f"{hs.district}, {hs.state}",
            confidence=round(hs.classification_confidence, 2),
            risk_score=hs.risk_score,
            status=status,
            assigned_officer=rng.choice(officers) if status != "new" else "",
            recommended_action=_recommended_action(hs.risk_level),
        ))
    db.commit()
    return alert_idx


def _alert_type(hs: Hotspot) -> str:
    if hs.classification == "Industrial Fire":
        return "industrial_fire"
    if hs.classification in ("Persistent Industrial Heat Source", "Gas Flare") and hs.persistence_score >= 55:
        return "persistent"
    if hs.classification == "Wildfire":
        return "wildfire"
    return "risk"


def _alert_title(hs: Hotspot) -> str:
    if hs.classification == "Industrial Fire":
        return f"Industrial fire detected near {hs.district}"
    if hs.classification == "Gas Flare":
        return "High-intensity gas flare signature detected"
    if hs.classification == "Persistent Industrial Heat Source":
        return f"Persistent thermal anomaly in {hs.district}"
    if hs.classification == "Wildfire":
        return f"Wildfire detected in {hs.state}"
    if hs.classification == "Agricultural Burning":
        return f"Agricultural burning detected in {hs.district}"
    return f"Thermal anomaly {hs.code} requires review"


def _alert_message(hs: Hotspot) -> str:
    return (
        f"{hs.code} classified as {hs.classification} with {int(hs.classification_confidence * 100)}% confidence. "
        f"Risk score {hs.risk_score:.0f}/100 ({hs.risk_level}). Detected at {hs.latitude:.4f}, {hs.longitude:.4f}."
    )


def _recommended_action(level: str) -> str:
    return {
        "CRITICAL": "Immediate field verification recommended.",
        "HIGH": "Priority inspection recommended.",
        "ELEVATED": "Enhanced monitoring recommended.",
        "MODERATE": "Continue monitoring.",
        "LOW": "No immediate action required.",
    }.get(level, "Continue monitoring.")


def seed_zones_risk(db, dataset) -> None:
    from app.gis.engine import haversine_km

    zones = db.query(IndustrialZone).all()
    hotspots = db.query(Hotspot).all()
    for z in zones:
        near = [
            h for h in hotspots
            if haversine_km(z.latitude, z.longitude, h.latitude, h.longitude) <= z.radius_km
        ]
        if not near:
            continue
        max_risk = max(h.risk_score for h in near)
        z.risk_level = risk_level_for(max_risk)
        if z.risk_level in ("CRITICAL", "HIGH"):
            z.monitoring_level = "INTENSIVE"
        elif z.risk_level == "ELEVATED":
            z.monitoring_level = "ELEVATED"
        settlements = dataset.points_within("settlement", z.latitude, z.longitude, 12.0)
        z.population_exposure = len(settlements) * 120000
    db.commit()


def seed_activity_and_notifications(db, users) -> None:
    actions = [
        ("login", "auth", "system"),
        ("data_ingestion", "firms", "system"),
        ("data_ingestion", "osm", "system"),
        ("data_ingestion", "landcover", "system"),
        ("classification", "hotspot", "system"),
        ("risk_update", "hotspot", "system"),
        ("alert_creation", "alert", "system"),
        ("report_generation", "report", "npgearly@gmail.com"),
    ]
    for action, entity, user in actions:
        db.add(ActivityLog(user=user, action=action, entity=entity, entity_id="", details={"seeded": True}))
    notification_service.notify(
        db,
        title="FIRE-X initialized",
        message="Fire intelligence environment initialized with FIRMS-like detections.",
        severity="info",
        entity="system",
    )
    db.commit()


def write_geojson_files(dataset) -> None:
    out = Path(settings.DATA_DIR)
    network = {"type": "FeatureCollection", "features": []}
    for cat, layer in (("road", "roads"), ("railway", "railways"), ("pipeline", "pipelines")):
        for g in dataset.geometries(cat):
            network["features"].append({
                "type": "Feature",
                "properties": {"name": g.name, "layer": layer},
                "geometry": _geom_to_geojson(g.geom),
            })
    (out / "network.geojson").write_text(json.dumps(network))

    landcover = {"type": "FeatureCollection", "features": []}
    for cat, layer in (("forest", "forest"), ("agriculture", "agriculture")):
        for g in dataset.geometries(cat):
            landcover["features"].append({
                "type": "Feature",
                "properties": {"name": g.name, "layer": layer, "state": g.meta.get("state", "")},
                "geometry": _geom_to_geojson(g.geom),
            })
    (out / "landcover.geojson").write_text(json.dumps(landcover))


def _geom_to_geojson(geom):
    from shapely.geometry import mapping

    return mapping(geom)


def main() -> None:
    init_db()
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        print("Wiping existing demo data...")
        wipe(db)
        print("Seeding users...")
        users = seed_users(db)
        print("Seeding industrial zones...")
        zones = seed_zones(db)
        zones_by_code = {z.code: z for z in zones}
        print("Building spatial dataset...")
        dataset = build_dataset()
        print("Seeding infrastructure...")
        seed_infrastructure(db, dataset, zones_by_code)
        print("Seeding hotspots (classification + risk)...")
        n_hotspots = seed_hotspots(db, dataset, now)
        print("Updating zone risk...")
        seed_zones_risk(db, dataset)
        print("Seeding activity log + notifications...")
        seed_activity_and_notifications(db, users)
        print("Writing GeoJSON reference files...")
        write_geojson_files(dataset)
        db.commit()

        zones = db.query(IndustrialZone).all()
        alerts = db.query(Alert).count()
        validations = db.query(SatelliteValidation).count()
        print(f"Done. {n_hotspots} hotspots | {len(zones)} zones | {alerts} alerts | {validations} satellite validations")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()