"""Risk scoring engine.

Factors (weighted 0-100 subscores):

- thermal intensity (brightness)
- FRP
- industrial proximity
- settlement proximity
- forest proximity
- agricultural proximity
- persistence
- satellite validation
- historical recurrence

Levels: LOW 0-20, MODERATE 21-40, ELEVATED 41-60, HIGH 61-80, CRITICAL 81-100.
"""
from __future__ import annotations

from typing import Any, Optional

from app.utils.helpers import clamp, risk_level_for

WEIGHTS = {
    "thermal_intensity": 0.20,
    "frp": 0.15,
    "industrial_proximity": 0.15,
    "settlement_proximity": 0.15,
    "forest_proximity": 0.08,
    "agriculture_proximity": 0.05,
    "persistence": 0.10,
    "satellite_validation": 0.07,
    "historical_recurrence": 0.05,
}

RECOMMENDATIONS = {
    "CRITICAL": "Immediate field verification recommended.",
    "HIGH": "Priority inspection recommended.",
    "ELEVATED": "Enhanced monitoring recommended.",
    "MODERATE": "Continue monitoring.",
    "LOW": "No immediate action required.",
}


def _subscore_linear(value: float, lo_val: float, hi_val: float) -> float:
    if value <= lo_val:
        return 0.0
    if value >= hi_val:
        return 100.0
    return (value - lo_val) / (hi_val - lo_val) * 100.0


def _industrial_subscore(dist_km: float) -> float:
    if dist_km < 0:
        return 10.0
    return _subscore_linear(dist_km, 0.0, 8.0) if dist_km <= 8.0 else 0.0


def _settlement_subscore(dist_km: float) -> float:
    if dist_km < 0:
        return 5.0
    return 100.0 - min(100.0, dist_km * 6.0)


def _forest_subscore(dist_km: float, classification: str) -> float:
    if dist_km < 0:
        return 10.0
    base = 100.0 - min(100.0, dist_km * 14.0)
    return base if classification in ("Wildfire", "Industrial Fire") else base * 0.6


def _agriculture_subscore(dist_km: float) -> float:
    if dist_km < 0:
        return 5.0
    return 100.0 - min(100.0, dist_km * 20.0)


def _satellite_subscore(status: Optional[str]) -> float:
    mapping = {"CONFIRMED": 90.0, "LIKELY": 70.0, "UNCERTAIN": 40.0, "NOT VALIDATED": 25.0, "": 25.0, None: 25.0}
    return mapping.get(status or "", 25.0)


def _recurrence_subscore(pattern: str) -> float:
    return {"persistent": 45.0, "recurring": 60.0, "sudden": 25.0, "intermittent": 35.0, "unknown": 15.0}.get(
        pattern, 15.0
    )


def compute_risk(
    *,
    brightness: float,
    frp: float,
    persistence_score: float,
    temporal_pattern: str,
    classification: str,
    nearest_industrial_km: float,
    nearest_settlement_km: float,
    nearest_forest_km: float,
    nearest_agriculture_km: float,
    satellite_status: Optional[str] = None,
    n_history: int = 0,
) -> dict[str, Any]:
    thermal = _subscore_linear(brightness, 300.0, 410.0)
    frp_score = min(100.0, frp * 1.1)
    industrial = _industrial_subscore(nearest_industrial_km)
    settlement = _settlement_subscore(nearest_settlement_km)
    forest = _forest_subscore(nearest_forest_km, classification)
    agriculture = _agriculture_subscore(nearest_agriculture_km)
    persistence = clamp(persistence_score)
    satellite = _satellite_subscore(satellite_status)
    recurrence = _recurrence_subscore(temporal_pattern)

    score = (
        thermal * WEIGHTS["thermal_intensity"]
        + frp_score * WEIGHTS["frp"]
        + industrial * WEIGHTS["industrial_proximity"]
        + settlement * WEIGHTS["settlement_proximity"]
        + forest * WEIGHTS["forest_proximity"]
        + agriculture * WEIGHTS["agriculture_proximity"]
        + persistence * WEIGHTS["persistence"]
        + satellite * WEIGHTS["satellite_validation"]
        + recurrence * WEIGHTS["historical_recurrence"]
    )

    # Classification-aware adjustments
    if classification == "Industrial Fire":
        score += 18.0
        if 0 <= nearest_settlement_km <= 5.0:
            score += 10.0  # population exposure to a possible industrial fire
    elif classification == "Gas Flare":
        score += 7.0
    elif classification == "Wildfire" and 0 <= nearest_settlement_km <= 5.0:
        score += 10.0
    elif classification == "Agricultural Burning":
        score -= 6.0

    score = clamp(score)
    level = risk_level_for(score)

    return {
        "score": round(score, 1),
        "level": level,
        "factors": {
            "thermal_intensity": round(thermal, 1),
            "frp": round(frp_score, 1),
            "industrial_proximity": round(industrial, 1),
            "settlement_proximity": round(settlement, 1),
            "forest_proximity": round(forest, 1),
            "agriculture_proximity": round(agriculture, 1),
            "persistence": round(persistence, 1),
            "satellite_validation": round(satellite, 1),
            "historical_recurrence": round(recurrence, 1),
        },
        "weights": dict(WEIGHTS),
        "recommendation": RECOMMENDATIONS.get(level, "Continue monitoring."),
        "trend": _build_trend(score, n_history, temporal_pattern),
    }


def _build_trend(score: float, n_history: int, pattern: str) -> list[float]:
    """Deterministic risk trend derived from the detection history."""
    if n_history <= 1:
        return [round(score, 1)]
    points = 4
    if pattern == "persistent":
        base = [score * 0.55, score * 0.7, score * 0.88, score]
    elif pattern == "recurring":
        base = [score * 0.5, score * 0.85, score * 0.6, score]
    elif pattern == "sudden":
        base = [score * 0.25, score * 0.5, score * 0.78, score]
    else:
        base = [score * 0.4, score * 0.6, score * 0.8, score]
    return [round(clamp(v), 1) for v in base[:points]]