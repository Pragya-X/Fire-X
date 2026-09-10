from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import ActivityLog, Alert, Notification, User
from app.schemas import AlertOut, AlertUpdate
from app.services.notification_service import notification_service
from app.services.sse import broadcast

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=dict)
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if status:
        q = q.filter(Alert.status == status)
    if severity:
        q = q.filter(Alert.severity == severity)
    if alert_type:
        q = q.filter(Alert.alert_type == alert_type)
    total = q.count()
    items = q.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [AlertOut.model_validate(a).model_dump() for a in items], "total": total}


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: int,
    body: AlertUpdate,
    user: User = Depends(require_role("field")),
    db: Session = Depends(get_db),
):
    a = db.get(Alert, alert_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if body.status:
        a.status = body.status
    if body.assigned_officer:
        a.assigned_officer = body.assigned_officer
    db.add(ActivityLog(user=user.email, action=f"alert_{a.status}", entity="alert", entity_id=a.code))
    db.commit()
    db.refresh(a)
    notification_service.notify(
        db,
        title=f"Alert {a.code} updated",
        message=f"{a.code} status changed to {a.status} by {user.name}.",
        severity="info", entity="alert", entity_id=a.code, user_id=user.id,
    )
    broadcast({"type": "alert_update", "data": AlertOut.model_validate(a).model_dump()})
    return AlertOut.model_validate(a)


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge(alert_id: int, user: User = Depends(require_role("field")), db: Session = Depends(get_db)):
    return _transition(alert_id, "acknowledged", user, db)


@router.post("/{alert_id}/escalate", response_model=AlertOut)
def escalate(alert_id: int, user: User = Depends(require_role("field")), db: Session = Depends(get_db)):
    return _transition(alert_id, "escalated", user, db)


@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve(alert_id: int, user: User = Depends(require_role("field")), db: Session = Depends(get_db)):
    return _transition(alert_id, "resolved", user, db)


def _transition(alert_id: int, new_status: str, user: User, db: Session) -> AlertOut:
    a = db.get(Alert, alert_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    a.status = new_status
    if not a.assigned_officer:
        a.assigned_officer = user.name
    db.add(ActivityLog(user=user.email, action=f"alert_{new_status}", entity="alert", entity_id=a.code))
    db.commit()
    db.refresh(a)
    notification_service.notify(
        db,
        title=f"Alert {a.code} {new_status}",
        message=f"{a.code} was {new_status} by {user.name}.",
        severity="info", entity="alert", entity_id=a.code, user_id=user.id,
    )
    broadcast({"type": "alert_update", "data": AlertOut.model_validate(a).model_dump()})
    return AlertOut.model_validate(a)


def _visible_notifications(db: Session, user: User):
    """Notifications addressed to the current user or broadcast globally."""
    return db.query(Notification).filter(
        (Notification.user_id == user.id) | (Notification.user_id.is_(None))
    )


@router.get("/notifications", response_model=dict)
def list_notifications(user: User = Depends(get_current_user), limit: int = 30, db: Session = Depends(get_db)):
    base = _visible_notifications(db, user)
    items = base.order_by(Notification.created_at.desc()).limit(limit).all()
    unread = base.filter(Notification.read == False).count()  # noqa: E712
    return {"items": [n.to_dict() for n in items], "unread": unread}


@router.post("/notifications/mark-read", response_model=dict)
def mark_notifications_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _visible_notifications(db, user).filter(Notification.read == False).update({"read": True})  # noqa: E712
    db.commit()
    return {"ok": True}


@router.post("/notifications/{notification_id}/read", response_model=dict)
def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.get(Notification, notification_id)
    if note is None or (note.user_id is not None and note.user_id != user.id):
        raise HTTPException(status_code=404, detail="Notification not found")
    note.read = True
    db.commit()
    return {"ok": True}