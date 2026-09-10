"""Database/SSE notifications and SMTP email; SMS requests report unavailable."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Notification
from app.services import mailer
from app.services.sse import broadcast


def _notify_in_app(
    db: Session,
    *,
    title: str,
    message: str,
    severity: str = "info",
    entity: str = "",
    entity_id: str = "",
    user_id: Optional[int] = None,
) -> dict:
    note = Notification(
        user_id=user_id,
        title=title,
        message=message,
        severity=severity,
        entity=entity,
        entity_id=entity_id,
    )
    db.add(note)
    db.flush()
    payload = note.to_dict()
    broadcast({"type": "notification", "data": payload})
    return payload


def _notify_email(
    *,
    title: str,
    message: str,
    to: Optional[str] = None,
) -> dict:
    recipients = settings.alert_recipients or ([to] if to else [])
    if not recipients:
        return {
            "provider": "email",
            "delivered": False,
            "reason": "No recipient (set MAIL_ALERT_RECIPIENTS or pass the acting user's email)",
        }
    alert_url = f"{settings.FRONTEND_URL.rstrip('/')}/alerts"
    results = []
    for recipient in recipients:
        results.append(
            mailer.send_alert_email(
                recipient,
                title=title,
                message=message,
                alert_url=alert_url,
            )
        )
    return {"provider": "email", "to": recipients, "results": results}


class NotificationService:
    def notify(
        self,
        db: Session,
        *,
        title: str,
        message: str,
        severity: str = "info",
        entity: str = "",
        entity_id: str = "",
        user_id: Optional[int] = None,
        to: Optional[str] = None,
        channels: Optional[list[str]] = None,
    ) -> list[dict]:
        from app.models import User
        channels = channels or ["in-app", "email"]
        
        # If no explicit 'to' address is provided but we have a user_id, resolve their email
        if "email" in channels and not to and user_id:
            user = db.get(User, user_id)
            if user:
                to = user.email

        sent = []
        for channel in channels:
            if channel == "in-app":
                sent.append(
                    _notify_in_app(
                        db, title=title, message=message, severity=severity,
                        entity=entity, entity_id=entity_id, user_id=user_id,
                    )
                )
            elif channel == "email":
                sent.append(
                    _notify_email(
                        title=title, message=message, to=to,
                    )
                )
            elif channel == "sms":
                payload = dict(title=title, message=message, severity=severity, entity=entity, entity_id=entity_id,
                               provider="sms-stub", delivered=False, reason="No SMS provider configured")
                broadcast({"type": "notification_stub", "data": payload})
                sent.append(payload)
        db.commit()
        return sent


notification_service = NotificationService()
