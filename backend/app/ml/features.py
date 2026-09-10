"""Feature engineering for the hotspot classifier.

Feature vector (in order - keep in sync with train_model.py and predict.py):

0  brightness            - VIIRS brightness temperature (Kelvin)
1  frp                   - fire radiative power (MW)
2  n_detections          - detections in the persistence window
3  persistence_score     - 0..100 temporal persistence score
4  dist_industrial_km    - distance to nearest industrial asset (km)
5  dist_forest_km        - distance to nearest forest polygon (km)
6  dist_agriculture_km   - distance to nearest agricultural polygon (km)
7  dist_settlement_km    - distance to nearest settlement (km)
8  land_cover_code       - Industrial=0 Forest=1 Agriculture=2 Urban=3 Barren=4 Other=5
9  time_of_day           - 0.0 (night) .. 1.0 (day)
10 historical_frequency  - detections per day over the window
11 satellite_score       - 0 none, 1 unlikely, 2 likely, 3 confirmed
12 frp_normalized        - frp / 160
13 brightness_normalized - (brightness - 300) / 120
"""
from __future__ import annotations

from typing import Any, Optional

FEATURE_NAMES = [
    "brightness",
    "frp",
    "n_detections",
    "persistence_score",
    "dist_industrial_km",
    "dist_forest_km",
    "dist_agriculture_km",
    "dist_settlement_km",
    "land_cover_code",
    "time_of_day",
    "historical_frequency",
    "satellite_score",
    "frp_normalized",
    "brightness_normalized",
]

LAND_COVER_CODES = {
    "Industrial": 0,
    "Forest": 1,
    "Agriculture": 2,
    "Urban": 3,
    "Barren": 4,
    "Other": 5,
}

CLASSES = [
    "Industrial Fire",
    "Persistent Industrial Heat Source",
    "Gas Flare",
    "Wildfire",
    "Agricultural Burning",
    "Other Thermal Anomaly",
]


def land_cover_code(land_cover: str) -> float:
    return float(LAND_COVER_CODES.get(land_cover, 5))


def satellite_score(validation_status: Optional[str]) -> float:
    if not validation_status:
        return 0.0
    mapping = {"NOT VALIDATED": 0.0, "UNCERTAIN": 1.0, "LIKELY": 2.0, "CONFIRMED": 3.0}
    return float(mapping.get(validation_status, 0.0))


def time_of_day_value(dt) -> float:
    """0.0 at midnight, 1.0 at solar noon, 0.0 at midnight again."""
    if dt is None:
        return 0.5
    hour = dt.hour + dt.minute / 60.0
    return max(0.0, min(1.0, 1.0 - abs(hour - 12.0) / 12.0))


def build_feature_vector(
    *,
    brightness: float,
    frp: float,
    n_detections: int,
    persistence_score: float,
    dist_industrial_km: float,
    dist_forest_km: float,
    dist_agriculture_km: float,
    dist_settlement_km: float,
    land_cover: str,
    acquisition_time,
    historical_frequency: float,
    validation_status: Optional[str],
) -> list[float]:
    b = max(0.0, float(brightness))
    f = max(0.0, float(frp))
    return [
        b,
        f,
        float(n_detections),
        float(persistence_score),
        max(-1.0, float(dist_industrial_km)),
        max(-1.0, float(dist_forest_km)),
        max(-1.0, float(dist_agriculture_km)),
        max(-1.0, float(dist_settlement_km)),
        land_cover_code(land_cover),
        time_of_day_value(acquisition_time),
        float(historical_frequency),
        satellite_score(validation_status),
        f / 160.0,
        (b - 300.0) / 120.0,
    ]


def explain_factors_from_vector(
    vector: list[float],
    classes_probs: dict[str, float],
    top_class: str,
    contextual: dict[str, Any],
) -> dict[str, Any]:
    """Build the explainable-AI payload: model-derived factors + rule-based context.

    The factor labels come from the feature vector; the contextual reasoning is
    produced by the rule engine (see ml/predict.py). The UI renders these two
    groups separately so it never presents heuristics as model explanations.
    """
    (b, f, n, persistence, d_ind, d_for, d_agr, d_set, lc, tod, hf, sat, _, _) = vector[:14]

    def label(value: float, thresholds: tuple[tuple[float, str], ...], default: str) -> str:
        for thr, lab in thresholds:
            if value <= thr:
                return lab
        return default

    thermal = label(b, ((310.0, "LOW"), (335.0, "MODERATE"), (360.0, "HIGH")), "VERY HIGH")
    frp_lab = label(f, ((15.0, "LOW"), (45.0, "MODERATE"), (90.0, "HIGH")), "VERY HIGH")
    ind_prox = label(d_ind, ((1.0, "VERY HIGH"), (3.0, "HIGH"), (8.0, "MODERATE")), "LOW") if d_ind >= 0 else "N/A"
    forest_prox = label(d_for, ((2.0, "VERY HIGH"), (6.0, "HIGH"), (15.0, "MODERATE")), "LOW") if d_for >= 0 else "N/A"
    agri_prox = label(d_agr, ((2.0, "VERY HIGH"), (6.0, "HIGH"), (15.0, "MODERATE")), "LOW") if d_agr >= 0 else "N/A"
    sett_prox = label(d_set, ((2.0, "VERY HIGH"), (6.0, "HIGH"), (15.0, "MODERATE")), "LOW") if d_set >= 0 else "N/A"
    persistence_lab = "HIGH" if persistence >= 55 else ("MODERATE" if persistence >= 25 else "LOW")
    recurrence_lab = "HIGH" if contextual.get("temporal_pattern") == "recurring" else (
        "MODERATE" if contextual.get("temporal_pattern") == "persistent" else "LOW"
    )
    sat_lab = contextual.get("satellite_validation") or "NOT VALIDATED"
    land_cover_names = {v: k for k, v in LAND_COVER_CODES.items()}
    lc_lab = land_cover_names.get(int(lc), "Other")

    model_factors = {
        "Thermal intensity": thermal,
        "FRP": frp_lab,
        "Industrial proximity": ind_prox,
        "Forest proximity": forest_prox,
        "Agricultural proximity": agri_prox,
        "Settlement proximity": sett_prox,
        "Persistence": persistence_lab,
        "Land cover": lc_lab,
        "Historical recurrence": recurrence_lab,
        "Satellite validation": sat_lab,
    }

    top_prob = classes_probs.get(top_class, 0.0)
    runner_up = sorted(classes_probs.items(), key=lambda kv: kv[1], reverse=True)
    runner = runner_up[1][0] if len(runner_up) > 1 else ""

    return {
        "top_class": top_class,
        "confidence": round(top_prob * 100, 1),
        "model_derived_factors": model_factors,
        "contextual_factors": contextual.get("contextual_factors", []),
        "reasoning": contextual.get("reasoning", ""),
        "probability_gap_pct": round((top_prob - (runner_up[1][1] if len(runner_up) > 1 else 0.0)) * 100, 1),
        "runner_up": runner,
    }