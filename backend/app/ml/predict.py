"""Explicit rule, synthetic demo and schema-validated real artifact inference."""
from __future__ import annotations

import math
import json
import logging
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

from app.config import settings
from app.ml.features import FEATURE_NAMES, CLASSES, explain_factors_from_vector

MODEL_PATH = Path(settings.MODEL_DIR) / "model.pkl"


# --------------------------------------------------------------------------
# Baseline rule engine
# --------------------------------------------------------------------------

def _score_clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _softmax(scores: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    exps = {k: math.exp(v / temperature) for k, v in scores.items()}
    total = sum(exps.values()) or 1.0
    return {k: v / total for k, v in exps.items()}


def rule_scores(vector: list[float]) -> dict[str, float]:
    """Score each class 0..~6 from the feature vector. Higher = more likely."""
    b, f, n, persistence, d_ind, d_for, d_agr, d_set, lc, tod, hf, sat, _, _ = vector[:14]

    industrial_close = d_ind >= 0 and d_ind < 8.0
    industrial_very_close = d_ind >= 0 and d_ind < 3.0
    forest_close = d_for >= 0 and d_for < 6.0
    agri_close = d_agr >= 0 and d_agr < 4.0
    in_industrial = lc == 0.0
    in_forest = lc == 1.0
    in_agri = lc == 2.0
    persistent = persistence >= 50.0 and n >= 4
    sudden = not persistent and n <= 2 and (b > 345.0 or f > 40.0)
    very_hot = b >= 360.0
    high_frp = f >= 60.0

    scores: dict[str, float] = {c: 0.05 for c in CLASSES}

    # Gas flare: persistent, extreme thermal source inside an industrial zone
    if persistent and very_hot and high_frp and (industrial_very_close or in_industrial):
        scores["Gas Flare"] += 4.0
        if d_ind < 1.0:
            scores["Gas Flare"] += 1.0
        if f >= 90.0:
            scores["Gas Flare"] += 1.0

    # Persistent industrial heat: steady repeated detections near industry
    if persistent and (industrial_close or in_industrial):
        scores["Persistent Industrial Heat Source"] += 3.5
        if industrial_very_close:
            scores["Persistent Industrial Heat Source"] += 1.0
        if not very_hot:
            scores["Persistent Industrial Heat Source"] += 0.5
        if n >= 8:
            scores["Persistent Industrial Heat Source"] += 0.5

    # Industrial fire: sudden intensity surge near infrastructure
    if sudden and (industrial_close or in_industrial) and (very_hot or high_frp):
        scores["Industrial Fire"] += 3.5
        if very_hot:
            scores["Industrial Fire"] += 0.75
        if high_frp:
            scores["Industrial Fire"] += 0.75
        if d_ind < 0.5:
            scores["Industrial Fire"] += 0.5

    # Wildfire: vegetated land, no industry, not inside an agricultural block
    if (forest_close or in_forest) and not industrial_close and not in_agri:
        scores["Wildfire"] += 3.0
        if in_forest:
            scores["Wildfire"] += 1.0
        if not sudden and n >= 3:
            scores["Wildfire"] += 0.5
        if d_ind < 0 or d_ind >= 8.0:
            scores["Wildfire"] += 0.5

    # Agricultural burning: crop land, moderate/low intensity, daylight
    if (agri_close or in_agri) and not in_forest:
        scores["Agricultural Burning"] += 3.0
        if in_agri:
            scores["Agricultural Burning"] += 1.5
        if not very_hot and not high_frp:
            scores["Agricultural Burning"] += 0.5
        if tod >= 0.5:
            scores["Agricultural Burning"] += 0.5
        if n <= 3:
            scores["Agricultural Burning"] += 0.25

    return scores


def rule_classify(vector: list[float]) -> dict[str, Any]:
    scores = rule_scores(vector)
    probs = _softmax(scores, temperature=1.2)
    top = max(probs, key=probs.get)
    # No rule fired: keep the detection as an unclassified anomaly instead of
    # defaulting to the first class in the list.
    if scores[top] <= 0.1:
        probs = {c: 0.05 for c in CLASSES}
        probs["Other Thermal Anomaly"] = 0.75
        total = sum(probs.values())
        probs = {c: p / total for c, p in probs.items()}
        top = "Other Thermal Anomaly"
    return {
        "classification": top,
        "confidence": probs[top],
        "probabilities": probs,
        "baseline": True,
    }


# --------------------------------------------------------------------------
# Model-backed prediction
# --------------------------------------------------------------------------

class _ModelCache:
    _model: Any = None
    _loaded: bool = False
    _path: str = ""
    _metadata: dict = {}
    _error: str | None = None
    _actual: str = "rules"


def load_model():
    """Load trusted local artifacts only; revalidate after file/config changes."""
    mode = settings.ML_MODE
    directory = Path(settings.MODEL_DIR)
    path = directory / ("classifier.joblib" if mode == "trained" else "model.pkl")
    metadata_path = directory / ("model_metadata.json" if mode == "trained" else "demo_metadata.json")
    signature = repr((mode, settings.ML_FALLBACK_MODE, str(path), [(p.stat().st_mtime_ns, p.stat().st_size) if p.exists() else None for p in (path, metadata_path, directory / "model.pkl")]))
    if _ModelCache._loaded and _ModelCache._path == signature:
        return _ModelCache._model
    _ModelCache._loaded, _ModelCache._path = True, signature
    _ModelCache._model, _ModelCache._metadata, _ModelCache._error = None, {}, None
    _ModelCache._actual = "rules"
    if mode == "rules":
        return None
    try:
        metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        if mode == "trained" and (metadata.get("training_data_type") != "real" or metadata.get("feature_names") != FEATURE_NAMES or not metadata.get("model_version")):
            raise ValueError("Real artifact metadata/feature schema incompatible or missing")
        model = joblib.load(path)
        if getattr(model, "n_features_in_", None) != len(FEATURE_NAMES):
            raise ValueError("Artifact feature count incompatible")
        names = getattr(model, "feature_names_in_", None)
        if names is not None and list(names) != FEATURE_NAMES:
            raise ValueError("Artifact feature order incompatible")
        classes = list(getattr(model, "classes_", []))
        if not classes or not all(isinstance(c, str) for c in classes):
            raise ValueError("Artifact class labels incompatible")
        if not hasattr(model, "predict_proba"):
            raise ValueError("Artifact lacks predict_proba")
        _ModelCache._model, _ModelCache._metadata = model, metadata
        _ModelCache._actual = mode
    except Exception as exc:
        _ModelCache._error = f"Artifact unavailable or incompatible ({type(exc).__name__})"
        logging.getLogger(__name__).warning(_ModelCache._error)
        if mode == "trained" and settings.ML_FALLBACK_MODE == "demo":
            try:
                demo = joblib.load(directory / "model.pkl")
                if getattr(demo, "n_features_in_", None) != len(FEATURE_NAMES) or not hasattr(demo, "predict_proba"):
                    raise ValueError("Demo schema incompatible")
                _ModelCache._model, _ModelCache._actual = demo, "demo"
            except Exception:
                _ModelCache._error += "; demo unavailable; using rules"
    return _ModelCache._model


def model_available() -> bool:
    return load_model() is not None


def model_predict(vector: list[float]) -> dict[str, Any]:
    model = load_model()
    if model is None:
        return rule_classify(vector)
    x = np.array([vector])
    proba = model.predict_proba(x)[0]
    # Align model classes (they may be a subset / different order)
    classes = list(getattr(model, "classes_", CLASSES))
    probs = {c: float(p) for c, p in zip(classes, proba)}
    for c in CLASSES:
        probs.setdefault(c, 0.0)
    total = sum(probs.values()) or 1.0
    probs = {c: p / total for c, p in probs.items()}
    top = max(probs, key=probs.get)
    return {
        "classification": top,
        "confidence": probs[top],
        "probabilities": probs,
        "baseline": False,
    }


# --------------------------------------------------------------------------
# Contextual reasoning
# --------------------------------------------------------------------------

CONTEXTUAL_REASONING = {
    "Industrial Fire": (
        "Hotspot is located close to industrial infrastructure and shows a sudden "
        "increase in thermal intensity. Repeated detections were not observed at "
        "this location before the current event. These factors increase the "
        "probability of an abnormal industrial fire."
    ),
    "Persistent Industrial Heat Source": (
        "Thermal detections repeatedly occur at nearly the same coordinates over "
        "multiple observation periods, with low temporal variability. The source "
        "is located inside or very near an industrial zone, consistent with "
        "operational heat rather than an uncontrolled fire."
    ),
    "Gas Flare": (
        "A very hot, high-FRP thermal source persists at a fixed location within "
        "an industrial facility. Continuous bright signatures of this kind are "
        "consistent with a gas flare or high-temperature industrial vent."
    ),
    "Wildfire": (
        "Hotspot overlaps or is near forest/vegetated land, has limited industrial "
        "infrastructure nearby, and exhibits spatial spread consistent with a "
        "natural vegetation fire."
    ),
    "Agricultural Burning": (
        "Hotspot occurs within agricultural land and shows a seasonal/spatial "
        "pattern consistent with crop-residue burning."
    ),
    "Other Thermal Anomaly": (
        "The detection does not clearly match an industrial, vegetated or "
        "agricultural signature. It may be a small transient heat source and is "
        "kept under observation."
    ),
}


def contextual_factors_for(classification: str, vector: list[float], temporal_pattern: str) -> list[str]:
    factors: list[str] = []
    b, f, n, persistence, d_ind, d_for, d_agr, d_set, lc, tod, hf, sat, _, _ = vector[:14]
    if classification == "Industrial Fire":
        if d_ind >= 0 and d_ind <= 0.5:
            factors.append("Industrial facility within 500 m")
        elif d_ind >= 0 and d_ind <= 3.0:
            factors.append("Industrial facility within 3 km")
        if n <= 2:
            factors.append("Sudden thermal intensity increase")
        if lc == 0.0:
            factors.append("Developed land cover")
        if persistence < 30:
            factors.append("Low persistence at this location")
        if d_for is None or d_for >= 8.0:
            factors.append("Low vegetation probability")
        if sat >= 2.0:
            factors.append("Satellite validation indicates possible smoke")
    elif classification == "Persistent Industrial Heat Source":
        factors.append(f"{n} detections over the observation window")
        factors.append("Low temporal variability")
        if d_ind >= 0 and d_ind <= 3.0:
            factors.append("Source inside industrial zone")
    elif classification == "Gas Flare":
        factors.append("Very high brightness temperature")
        factors.append("High FRP sustained over time")
        if d_ind >= 0:
            factors.append("Fixed location inside industrial facility")
    elif classification == "Wildfire":
        factors.append("Forest/vegetated land cover")
        if d_ind < 0 or d_ind >= 8.0:
            factors.append("No significant industrial infrastructure nearby")
        if n >= 3:
            factors.append("Multiple detections consistent with spread")
        if d_set >= 0 and d_set <= 5.0:
            factors.append("Settlement exposure within 5 km")
    elif classification == "Agricultural Burning":
        factors.append("Detection within agricultural land")
        if tod >= 0.5:
            factors.append("Daytime detection typical of residue burning")
        if n <= 3:
            factors.append("Short-lived, low-intensity signature")
    else:
        factors.append("Signature does not match known categories")
    return factors


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def classify_vector(
    vector: list[float],
    *,
    temporal_pattern: str = "unknown",
    satellite_validation: Optional[str] = None,
) -> dict[str, Any]:
    """Full classification pipeline for a single feature vector."""
    result = model_predict(vector)
    health = classification_health()

    classification = result["classification"]
    probs = result["probabilities"]
    contextual = {
        "temporal_pattern": temporal_pattern,
        "satellite_validation": satellite_validation or "NOT VALIDATED",
        "contextual_factors": contextual_factors_for(classification, vector, temporal_pattern),
        "reasoning": CONTEXTUAL_REASONING.get(classification, ""),
    }
    explanation = explain_factors_from_vector(vector, probs, classification, contextual)
    provenance = {k: health[k] for k in ("model_mode", "requested_mode", "model_version", "training_data_type", "fallback_reason")}
    explanation.update(provenance)
    explanation["factor_type"] = "heuristic_context"
    explanation["probability_type"] = "uncalibrated_model_probability" if not result["baseline"] else "heuristic_score"
    return {
        "classification": classification,
        "confidence": result["confidence"],
        "probabilities": probs,
        "explanation": explanation,
        "baseline": result.get("baseline", True),
        **provenance,
    }


def classification_health() -> dict:
    model = load_model()
    requested = settings.ML_MODE
    actual = _ModelCache._actual
    fallback_reason = _ModelCache._error
    metadata = _ModelCache._metadata
    path = Path(settings.MODEL_DIR) / ("classifier.joblib" if actual == "trained" else "model.pkl")
    metrics_path = Path(settings.MODEL_DIR) / "metrics.json"
    evaluation = None
    if model is not None and metrics_path.exists():
        try:
            candidate = json.loads(metrics_path.read_text())
            if actual == "demo" or (candidate.get("training_data_type") == "real" and candidate.get("model_version") == metadata.get("model_version")):
                evaluation = candidate
        except (ValueError, OSError):
            pass
    return {
        "status": "baseline" if actual == "rules" else ("demo" if actual == "demo" else "online"),
        "mode": {"rules": "RULE FALLBACK", "demo": "DEMO MODEL", "trained": "REAL TRAINED MODEL"}[actual],
        "model_mode": {"rules": "RULES", "demo": "DEMO_MODEL", "trained": "TRAINED_MODEL"}[actual],
        "requested_mode": requested, "artifact_path": str(path) if model is not None else None, "model_file": str(path),
        "model_version": metadata.get("model_version", "rules-v1" if actual == "rules" else "legacy-demo"),
        "training_data_type": "none" if actual == "rules" else ("synthetic" if actual == "demo" else "real"),
        "evaluation_available": evaluation is not None, "evaluation": evaluation,
        "evaluation_data_type": ("synthetic" if actual == "demo" else "real") if evaluation is not None else None,
        "fallback_reason": fallback_reason,
    }
