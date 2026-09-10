from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CopilotRequest, CopilotResponse
from app.services.copilot import SUGGESTED_QUESTIONS, ask

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


@router.post("/ask", response_model=CopilotResponse)
def copilot_ask(body: CopilotRequest, db: Session = Depends(get_db)):
    result = ask(db, body.question.strip())
    return CopilotResponse(
        answer=result["answer"],
        mode=result["mode"],
        intents=result.get("intents", ["query"]),
        data=result.get("data"),
    )


@router.get("/suggestions")
def suggestions():
    return {"items": SUGGESTED_QUESTIONS}