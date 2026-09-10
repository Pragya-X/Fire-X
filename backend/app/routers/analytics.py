"""Read-only dashboard statistics and history."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Alert, Hotspot, IndustrialZone
from app.utils.helpers import CLASSIFICATIONS
from typing import Optional


router = APIRouter(prefix="/api/v1")


@router.get("/analytics", tags=['analytics'], response_model=dict)
def analytics(db: Session = Depends(get_db)):
    """All analytics charts in one payload (frontend charts use only this data)."""
    now = datetime.now(timezone.utc)

    by_class = dict(db.query(Hotspot.classification, func.count()).group_by(Hotspot.classification).all())
    by_state = dict(db.query(Hotspot.state, func.count()).group_by(Hotspot.state).all())
    by_district = dict(db.query(Hotspot.district, func.count()).group_by(Hotspot.district).all())
    by_risk = dict(db.query(Hotspot.risk_level, func.count()).group_by(Hotspot.risk_level).all())

    daily = _series(db, now, "day", 14)
    weekly = _series(db, now, "week", 12)
    monthly = _series(db, now, "month", 12)

    classification_series = _classification_series(db, now)

    # Industrial vs wildfire trend (7-day buckets)
    ind_vs_wf = []
    for i in range(7, -1, -1):
        start = now - timedelta(days=i + 1)
        end = now - timedelta(days=i)
        ind = db.query(Hotspot).filter(
            Hotspot.acquisition_time >= start, Hotspot.acquisition_time < end,
            Hotspot.classification.in_(["Industrial Fire", "Persistent Industrial Heat Source", "Gas Flare"]),
        ).count()
        wf = db.query(Hotspot).filter(
            Hotspot.acquisition_time >= start, Hotspot.acquisition_time < end,
            Hotspot.classification == "Wildfire",
        ).count()
        ind_vs_wf.append({"date": start.date().isoformat(), "industrial": ind, "wildfire": wf})

    avg_conf = db.query(func.avg(Hotspot.classification_confidence)).scalar() or 0
    avg_risk = db.query(func.avg(Hotspot.risk_score)).scalar() or 0

    top_zones = db.query(IndustrialZone).order_by(IndustrialZone.risk_level.desc()).limit(10).all()
    top_zone_data = [
        {"name": z.name, "type": z.zone_type, "risk_level": z.risk_level, "monitoring": z.monitoring_level}
        for z in top_zones
    ]

    recurring = (
        db.query(Hotspot)
        .filter(Hotspot.temporal_pattern.in_(["recurring", "persistent"]))
        .order_by(Hotspot.persistence_score.desc())
        .limit(10)
        .all()
    )
    recurring_data = [
        {"code": h.code, "persistence_score": h.persistence_score, "classification": h.classification, "state": h.state}
        for h in recurring
    ]

    alert_status = dict(db.query(Alert.status, func.count()).group_by(Alert.status).all())

    return {
        "by_classification": [{"name": c, "value": by_class.get(c, 0)} for c in CLASSIFICATIONS],
        "by_state": _topn(by_state, 12),
        "by_district": _topn(by_district, 12),
        "by_risk": [{"name": lv, "value": by_risk.get(lv, 0)} for lv in ["LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"]],
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "classification_series": classification_series,
        "industrial_vs_wildfire": ind_vs_wf,
        "top_industrial_zones": top_zone_data,
        "top_recurring_hotspots": recurring_data,
        "avg_classification_confidence": round(float(avg_conf or 0) * 100, 1),
        "avg_risk_score": round(float(avg_risk or 0), 1),
        "alert_status": alert_status,
        "generated_at": now.isoformat(),
    }


def _topn(counter: dict, n: int) -> list[dict]:
    return [{"name": k, "value": v} for k, v in sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:n]]


def _series(db: Session, now: datetime, bucket: str, points: int) -> list[dict]:
    out = []
    if bucket == "day":
        for i in range(points - 1, -1, -1):
            start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            n = db.query(Hotspot).filter(Hotspot.acquisition_time >= start, Hotspot.acquisition_time < end).count()
            out.append({"label": start.strftime("%b %d"), "count": n})
    elif bucket == "week":
        for i in range(points - 1, -1, -1):
            start = now - timedelta(days=i * 7)
            end = start + timedelta(days=7)
            n = db.query(Hotspot).filter(Hotspot.acquisition_time >= start, Hotspot.acquisition_time < end).count()
            out.append({"label": start.strftime("%b %d"), "count": n})
    else:
        for i in range(points - 1, -1, -1):
            start = now - timedelta(days=30 * i)
            end = start + timedelta(days=30)
            n = db.query(Hotspot).filter(Hotspot.acquisition_time >= start, Hotspot.acquisition_time < end).count()
            out.append({"label": start.strftime("%b %y"), "count": n})
    return out


def _classification_series(db: Session, now: datetime) -> list[dict]:
    out = []
    for i in range(13, -1, -1):
        start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        rows = (
            db.query(Hotspot.classification, func.count())
            .filter(Hotspot.acquisition_time >= start, Hotspot.acquisition_time < end)
            .group_by(Hotspot.classification)
            .all()
        )
        out.append(
            {
                "date": start.strftime("%b %d"),
                **{c: 0 for c in CLASSIFICATIONS},
                **{c: n for c, n in rows},
            }
        )
    return out


@router.get("/historical", tags=['historical'], response_model=dict)
def historical_records(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    state: Optional[str] = None,
    classification: Optional[str] = None,
    risk: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Hotspot)
    if date_from:
        q = q.filter(Hotspot.acquisition_time >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(Hotspot.acquisition_time <= datetime.fromisoformat(date_to))
    if state:
        q = q.filter(Hotspot.state == state)
    if classification:
        q = q.filter(Hotspot.classification == classification)
    if risk:
        q = q.filter(Hotspot.risk_level == risk)
    total = q.count()
    items = q.order_by(Hotspot.acquisition_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [h.to_dict() for h in items], "total": total}


@router.get("/historical/playback", tags=['historical'])
def playback_days(
    days: int = Query(14, ge=1, le=60),
    db: Session = Depends(get_db),
):
    """Per-day hotspot snapshots for map playback."""
    now = datetime.now(timezone.utc)
    frames = []
    for i in range(days - 1, -1, -1):
        start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        rows = db.query(Hotspot).filter(Hotspot.acquisition_time >= start, Hotspot.acquisition_time < end).all()
        frames.append(
            {
                "date": start.date().isoformat(),
                "label": start.strftime("%b %d"),
                "count": len(rows),
                "hotspots": [
                    {
                        "code": h.code, "latitude": h.latitude, "longitude": h.longitude,
                        "classification": h.classification, "risk_level": h.risk_level,
                        "risk_score": h.risk_score, "brightness": h.brightness, "frp": h.frp,
                    }
                    for h in rows
                ],
            }
        )
    return {"frames": frames}


@router.get("/historical/recurring", tags=['historical'], response_model=dict)
def recurring_hotspots(db: Session = Depends(get_db)):
    rows = (
        db.query(Hotspot)
        .filter(Hotspot.temporal_pattern.in_(["recurring", "persistent"]))
        .order_by(Hotspot.persistence_score.desc())
        .limit(25)
        .all()
    )
    return {"items": [h.to_dict() for h in rows], "total": len(rows)}


@router.get("/historical/timeline", tags=['historical'], response_model=dict)
def timeline_summary(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(func.date(Hotspot.acquisition_time).label("d"), func.count())
        .filter(Hotspot.acquisition_time >= start)
        .group_by("d")
        .all()
    )
    return {"timeline": [{"date": str(d), "count": n} for d, n in rows]}
