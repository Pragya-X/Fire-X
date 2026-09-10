from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.models import ActivityLog, Hotspot, IndustrialZone, User
from app.services.report_service import build_daily_report, build_incident_report, build_zone_report

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/incident/{hotspot_id}")
def incident_report(hotspot_id: int, user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    h = db.get(Hotspot, hotspot_id)
    if h is None:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    pdf = build_incident_report(db, h)
    db.add(ActivityLog(user=user.email, action="report_generation", entity="report", entity_id=h.code))
    db.commit()
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{h.code}-incident-report.pdf"'},
    )


@router.get("/daily")
def daily_report(days: int = Query(1, ge=1, le=30), user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    pdf = build_daily_report(db, days)
    db.add(ActivityLog(user=user.email, action="report_generation", entity="report", entity_id=f"daily-{days}d"))
    db.commit()
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="firex-daily-report.pdf"'},
    )


@router.get("/zone/{zone_id}")
def zone_report(zone_id: int, user: User = Depends(require_role("analyst")), db: Session = Depends(get_db)):
    z = db.get(IndustrialZone, zone_id)
    if z is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    pdf = build_zone_report(db, z)
    db.add(ActivityLog(user=user.email, action="report_generation", entity="report", entity_id=z.code))
    db.commit()
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{z.code}-zone-report.pdf"'},
    )