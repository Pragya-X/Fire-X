from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ActivityLog, User
from app.services.sse import event_generator

router = APIRouter(prefix="/api/v1")


@router.get("/activity", response_model=dict, tags=["activity"])
def list_activity(
    action: str | None = None,
    limit: int = 100,
    scope: str = "self",
    user: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activity log for the current user; admins may request every user's rows.

    ``scope=self`` (default) returns only the caller's activity. ``scope=all``
    is admin-only and returns the full audit trail, optionally narrowed to a
    single account via ``user=<email>``.
    """
    q = db.query(ActivityLog)
    if scope == "all":
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required for scope=all")
        if user:
            q = q.filter(ActivityLog.user == user)
    else:
        # Regular users only ever see their own activity.
        q = q.filter(ActivityLog.user == current_user.email)
    if action:
        q = q.filter(ActivityLog.action == action)
    items = q.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return {"items": [a.to_dict() for a in items], "total": len(items)}


@router.get("/events/stream", tags=["events"])
async def stream(request: Request):
    async def gen():
        async for msg in event_generator():
            if await request.is_disconnected():
                break
            yield msg

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
