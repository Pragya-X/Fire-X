from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Hotspot, InfrastructureFeature
from app.schemas import HotspotDetailOut, HotspotOut
from app.services.report_service import build_daily_report, build_incident_report

router = APIRouter(prefix="/api/v1/hotspots", tags=["hotspots"])

RISK_COLORS = {
    "CRITICAL": "#ef4444",
    "HIGH": "#f97316",
    "ELEVATED": "#eab308",
    "MODERATE": "#3b82f6",
    "LOW": "#22c55e",
}


def _apply_filters(q, db: Session, **params):
    if params.get("classification"):
        q = q.filter(Hotspot.classification == params["classification"])
    if params.get("risk"):
        q = q.filter(Hotspot.risk_level == params["risk"])
    if params.get("min_confidence") is not None:
        q = q.filter(Hotspot.classification_confidence >= params["min_confidence"])
    if params.get("state"):
        q = q.filter(Hotspot.state == params["state"])
    if params.get("district"):
        q = q.filter(Hotspot.district == params["district"])
    if params.get("status"):
        q = q.filter(Hotspot.status == params["status"])
    if params.get("temporal_pattern"):
        q = q.filter(Hotspot.temporal_pattern == params["temporal_pattern"])
    if params.get("date_from"):
        q = q.filter(Hotspot.acquisition_time >= datetime.fromisoformat(params["date_from"]))
    if params.get("date_to"):
        q = q.filter(Hotspot.acquisition_time <= datetime.fromisoformat(params["date_to"]))
    if params.get("search"):
        term = params["search"].strip()
        like = f"%{term}%"
        q = q.filter(or_(Hotspot.code.ilike(like), Hotspot.state.ilike(like), Hotspot.district.ilike(like)))
    # proximity filters join infrastructure_features
    prox = {
        "industrial_proximity": "nearest_refinery_distance",
        "forest_proximity": "nearest_forest_distance",
        "agriculture_proximity": "nearest_agriculture_distance",
        "settlement_proximity": "nearest_settlement_distance",
    }
    joins = set()
    for key, col in prox.items():
        if params.get(key) is not None:
            if "ftr" not in joins:
                q = q.join(InfrastructureFeature, InfrastructureFeature.hotspot_id == Hotspot.id)
                joins.add("ftr")
            col_obj = getattr(InfrastructureFeature, col)
            q = q.filter(col_obj <= params[key])
    return q


@router.get("", response_model=dict)
def list_hotspots(
    classification: Optional[str] = None,
    risk: Optional[str] = None,
    min_confidence: Optional[float] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    status: Optional[str] = None,
    temporal_pattern: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    industrial_proximity: Optional[float] = None,
    forest_proximity: Optional[float] = None,
    agriculture_proximity: Optional[float] = None,
    settlement_proximity: Optional[float] = None,
    search: Optional[str] = None,
    sort: str = "acquisition_time",
    order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Hotspot)
    q = _apply_filters(
        q, db,
        classification=classification, risk=risk, min_confidence=min_confidence,
        state=state, district=district, status=status, temporal_pattern=temporal_pattern,
        date_from=date_from, date_to=date_to, search=search,
        industrial_proximity=industrial_proximity, forest_proximity=forest_proximity,
        agriculture_proximity=agriculture_proximity, settlement_proximity=settlement_proximity,
    )
    total = q.count()
    col = getattr(Hotspot, sort, Hotspot.acquisition_time)
    q = q.order_by(col.desc() if order == "desc" else col.asc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [HotspotOut.model_validate(i).model_dump() for i in items], "total": total, "page": page, "page_size": page_size}


@router.get("/stats", response_model=dict)
def hotspot_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func

    total = db.query(Hotspot).count()
    by_risk = dict(db.query(Hotspot.risk_level, func.count()).group_by(Hotspot.risk_level).all())
    by_class = dict(db.query(Hotspot.classification, func.count()).group_by(Hotspot.classification).all())
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    prev_week = week_ago - timedelta(days=7)
    current_week = db.query(Hotspot).filter(Hotspot.acquisition_time >= week_ago).count()
    previous_week = db.query(Hotspot).filter(
        Hotspot.acquisition_time >= prev_week, Hotspot.acquisition_time < week_ago
    ).count()

    def pct(cur: int, prev: int) -> float:
        if prev == 0:
            return 0.0
        return round((cur - prev) / prev * 100, 1)

    return {
        "total": total,
        "by_risk": by_risk,
        "by_classification": by_class,
        "critical": by_risk.get("CRITICAL", 0),
        "high": by_risk.get("HIGH", 0),
        "industrial_fires": by_class.get("Industrial Fire", 0),
        "wildfires": by_class.get("Wildfire", 0),
        "agricultural_burns": by_class.get("Agricultural Burning", 0),
        "persistent_sources": by_class.get("Persistent Industrial Heat Source", 0) + by_class.get("Gas Flare", 0),
        "week_change_pct": pct(current_week, previous_week),
        "industrial_fire_change_pct": 0.0,
    }


@router.get("/geojson")
def hotspots_geojson(
    classification: Optional[str] = None,
    risk: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Hotspot)
    q = _apply_filters(q, db, classification=classification, risk=risk, state=state)
    items = q.all()
    features = []
    for h in items:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [h.longitude, h.latitude]},
                "properties": {
                    "id": h.id,
                    "code": h.code,
                    "classification": h.classification,
                    "risk_level": h.risk_level,
                    "risk_score": h.risk_score,
                    "confidence": h.classification_confidence,
                    "brightness": h.brightness,
                    "frp": h.frp,
                    "state": h.state,
                    "district": h.district,
                    "acquisition_time": h.acquisition_time.isoformat() if h.acquisition_time else None,
                    "color": RISK_COLORS.get(h.risk_level, "#64748b"),
                    "persistence_score": h.persistence_score,
                    "temporal_pattern": h.temporal_pattern,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


@router.get("/export")
def export_hotspots(
    format: str = Query("csv", pattern="^(csv|json|geojson|pdf)$"),
    classification: Optional[str] = None,
    risk: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Hotspot)
    q = _apply_filters(q, db, classification=classification, risk=risk, state=state)
    items = q.all()

    if format == "geojson":
        fc = hotspots_geojson(classification=classification, risk=risk, state=state, db=db)
        return Response(json.dumps(fc, default=str), media_type="application/geo+json")

    if format == "json":
        data = [h.to_dict() for h in items]
        return Response(json.dumps(data, default=str), media_type="application/json")

    if format == "pdf":
        pdf = build_daily_report(db)
        return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=firex-hotspots-report.pdf"})

    # CSV
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["code", "classification", "risk_level", "risk_score", "confidence", "brightness", "frp",
         "latitude", "longitude", "state", "district", "acquisition_time", "persistence_score", "status"]
    )
    for h in items:
        writer.writerow(
            [h.code, h.classification, h.risk_level, h.risk_score, h.classification_confidence,
             h.brightness, h.frp, h.latitude, h.longitude, h.state, h.district,
             h.acquisition_time.isoformat() if h.acquisition_time else "", h.persistence_score, h.status]
        )
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=firex-hotspots.csv"})


@router.get("/{hotspot_id}", response_model=dict)
def get_hotspot(hotspot_id: int, db: Session = Depends(get_db)):
    h = db.query(Hotspot).options(joinedload(Hotspot.features), joinedload(Hotspot.history), joinedload(Hotspot.validations)).filter(Hotspot.id == hotspot_id).first()
    if h is None:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    data = HotspotDetailOut.model_validate(h).model_dump()
    data["features"] = h.features.to_dict() if h.features else None
    data["history"] = [x.to_dict() for x in sorted(h.history, key=lambda x: x.detection_time)]
    data["validations"] = [v.to_dict() for v in h.validations]
    return data


@router.get("/{hotspot_id}/report")
def hotspot_report(hotspot_id: int, db: Session = Depends(get_db)):
    h = db.get(Hotspot, hotspot_id)
    if h is None:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    pdf = build_incident_report(db, h)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={h.code}-incident-report.pdf"},
    )