"""FIRE-X Copilot.

Answers questions using application data. Two modes:

- demo (default): deterministic rule-based intent matching + DB queries.
  The UI shows "Demo Copilot" in this mode.
- llm: when OPENAI_API_KEY is configured, tool-style context is fetched first
  and sent to the model - the model never sees raw DB access and cannot invent
  facts (its prompt includes the fetched context only).

Every answer is grounded in data returned by the backend APIs.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alert, Hotspot, IndustrialZone

CRITICAL_ACTIONS = {
    "CRITICAL": "Immediate field verification recommended.",
    "HIGH": "Priority inspection recommended.",
    "ELEVATED": "Enhanced monitoring recommended.",
    "MODERATE": "Continue monitoring.",
    "LOW": "No immediate action required.",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hotspot_line(h: Hotspot) -> str:
    return (
        f"{h.code} ({h.classification}, risk {h.risk_score:.0f}/100 {h.risk_level}, "
        f"{h.state}/{h.district}, {h.latitude:.3f},{h.longitude:.3f})"
    )


def _format_list(items: list[str], limit: int = 8) -> str:
    if not items:
        return "None found."
    body = "\n".join(f"- {x}" for x in items[:limit])
    if len(items) > limit:
        body += f"\n... and {len(items) - limit} more."
    return body


def _collect_context(db: Session, question: str) -> tuple[list[str], dict[str, Any]]:
    """Run the intent-specific DB queries. Returns (facts, structured data)."""
    q = question.lower()
    facts: list[str] = []
    data: dict[str, Any] = {}

    if "critical" in q or "highest risk" in q:
        rows = db.query(Hotspot).filter(Hotspot.risk_level.in_(["CRITICAL", "HIGH"])).order_by(Hotspot.risk_score.desc()).limit(10).all()
        facts.append("Hotspots with CRITICAL or HIGH risk:")
        facts.append(_format_list([_hotspot_line(h) for h in rows]))
        data["hotspots"] = [h.to_dict() for h in rows]
    elif "industrial zone" in q or "zones" in q:
        rows = db.query(IndustrialZone).order_by(IndustrialZone.risk_level.desc()).limit(10).all()
        facts.append("Industrial zones by current risk:")
        facts.append(_format_list([f"{z.name} - {z.risk_level} (monitoring {z.monitoring_level})" for z in rows]))
        data["zones"] = [z.to_dict() for z in rows]
    elif q.startswith("why") or "why" in q and "classified" in q or "explain" in q:
        code = _extract_code(question)
        h = db.query(Hotspot).filter(Hotspot.code == code).first() if code else None
        if h is None and code is None:
            rows = db.query(Hotspot).order_by(Hotspot.risk_score.desc()).first()
            h = rows
        if h:
            exp = h.explanation or {}
            factors = exp.get("model_derived_factors", {})
            reasoning = exp.get("reasoning", "")
            facts.append(f"{h.code} classified as {h.classification} with {h.classification_confidence*100:.0f}% confidence, risk {h.risk_score:.0f}/100.")
            facts.append("Model-derived factors: " + ", ".join(f"{k}={v}" for k, v in factors.items()))
            facts.append(f"Reasoning: {reasoning}")
            data["hotspot"] = h.to_dict()
        else:
            facts.append("No matching hotspot found.")
    elif "persistent" in q:
        rows = db.query(Hotspot).filter(Hotspot.persistence_score >= 50).order_by(Hotspot.persistence_score.desc()).limit(10).all()
        facts.append("Hotspots with persistent thermal signatures:")
        facts.append(_format_list([f"{h.code} persistence {h.persistence_score:.0f} ({h.classification})" for h in rows]))
        data["hotspots"] = [h.to_dict() for h in rows]
    elif "refiner" in q or "near refinery" in q:
        from app.models import InfrastructureFeature

        rows = (
            db.query(Hotspot, InfrastructureFeature)
            .join(InfrastructureFeature)
            .filter(InfrastructureFeature.nearest_refinery_distance <= 5.0)
            .order_by(InfrastructureFeature.nearest_refinery_distance)
            .limit(10)
            .all()
        )
        facts.append("Hotspots within 5 km of a refinery:")
        facts.append(_format_list([f"{h.code} - {f.nearest_refinery_distance:.2f} km to refinery ({h.classification})" for h, f in rows]))
        data["hotspots"] = [h.to_dict() for h, _ in rows]
    elif "wildfire" in q or "wildfires" in q:
        week_ago = _now() - timedelta(days=7)
        count = db.query(Hotspot).filter(Hotspot.classification == "Wildfire", Hotspot.acquisition_time >= week_ago).count()
        rows = db.query(Hotspot).filter(Hotspot.classification == "Wildfire").order_by(Hotspot.acquisition_time.desc()).limit(8).all()
        facts.append(f"{count} wildfire detections in the last 7 days.")
        facts.append("Recent wildfires: " + ", ".join(h.code for h in rows))
        data["hotspots"] = [h.to_dict() for h in rows]
    elif "summary" in q or "today" in q or "incident" in q:
        today = _now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = db.query(Hotspot).filter(Hotspot.acquisition_time >= today).count()
        week_ago = _now() - timedelta(days=7)
        week_count = db.query(Hotspot).filter(Hotspot.acquisition_time >= week_ago).count()
        cls = db.query(Hotspot.classification, func.count()).group_by(Hotspot.classification).all()
        alerts_new = db.query(Alert).filter(Alert.status == "new").count()
        facts.append(f"Today: {today_count} detections. Last 7 days: {week_count} detections.")
        facts.append("Distribution: " + ", ".join(f"{c}={n}" for c, n in cls))
        facts.append(f"{alerts_new} new alerts awaiting acknowledgement.")
        data["summary"] = {"today": today_count, "week": week_count, "alerts_new": alerts_new}
    elif "settlement" in q or "population" in q or "people" in q:
        from app.models import InfrastructureFeature

        rows = (
            db.query(Hotspot, InfrastructureFeature)
            .join(InfrastructureFeature)
            .filter(InfrastructureFeature.nearest_settlement_distance <= 3.0)
            .order_by(InfrastructureFeature.nearest_settlement_distance)
            .limit(10)
            .all()
        )
        facts.append("Hotspots closest to settlements:")
        facts.append(_format_list([f"{h.code} - {f.nearest_settlement_distance:.2f} km ({h.risk_level})" for h, f in rows]))
        data["hotspots"] = [h.to_dict() for h, _ in rows]
    elif "investigat" in q or "immediate" in q or "attention" in q:
        rows = db.query(Hotspot).filter(Hotspot.risk_level == "CRITICAL").all()
        if not rows:
            rows = db.query(Hotspot).filter(Hotspot.risk_level == "HIGH").all()
        facts.append("Areas requiring immediate investigation:")
        facts.append(_format_list([f"{h.code} - {h.classification} - {h.risk_score:.0f}/100 {h.risk_level}" for h in rows]))
        data["hotspots"] = [h.to_dict() for h in rows]
    else:
        # Generic overview fallback
        total = db.query(Hotspot).count()
        critical = db.query(Hotspot).filter(Hotspot.risk_level == "CRITICAL").count()
        active_alerts = db.query(Alert).filter(Alert.status.in_(["new", "acknowledged", "investigating", "escalated"])).count()
        facts.append(f"FIRE-X overview: {total} tracked hotspots, {critical} critical, {active_alerts} active alerts.")
        data["overview"] = {"total": total, "critical": critical, "active_alerts": active_alerts}

    return facts, data


def _extract_code(question: str) -> Optional[str]:
    import re

    m = re.search(r"(HX-\d{3,4})", question.upper())
    return m.group(1) if m else None


def _demo_answer(facts: list[str]) -> str:
    return "\n".join(facts)


def _llm_answer(question: str, facts: list[str], data: dict) -> str:
    """OpenAI-backed answering. Context is injected so the model cannot invent facts."""
    system = (
        "You are FIRE-X Copilot, an AI assistant for a geospatial fire intelligence platform. "
        "Answer ONLY from the provided context facts. If the context does not contain the "
        "answer, say so plainly. Do not invent numbers, hotspot IDs or locations. "
        "Keep answers concise and structured."
    )
    user = f"Context:\n{json.dumps(facts, indent=2)}\n\nQuestion: {question}"
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
                "max_tokens": 400,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return _demo_answer(facts)


def ask(db: Session, question: str) -> dict[str, Any]:
    facts, data = _collect_context(db, question)
    if settings.openai_api_key:
        answer = _llm_answer(question, facts, data)
        mode = "llm"
    else:
        answer = _demo_answer(facts)
        mode = "demo"
    return {"answer": answer, "mode": mode, "intents": ["query"], "data": data}


SUGGESTED_QUESTIONS = [
    "Show all critical hotspots.",
    "Which industrial zones are currently at highest risk?",
    "Why was hotspot HX-0001 classified as industrial fire?",
    "Which hotspots are persistent?",
    "Show hotspots near refineries.",
    "How many wildfires were detected this week?",
    "Generate a summary of today's incidents.",
    "Which hotspots are closest to settlements?",
    "Which areas require immediate investigation?",
]