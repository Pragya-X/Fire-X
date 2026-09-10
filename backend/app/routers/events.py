from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ActivityLog
from app.services.sse import event_generator

router = APIRouter(prefix="/api/v1")


@router.get("/activity", response_model=dict, tags=["activity"])
def list_activity(action: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(ActivityLog)
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
