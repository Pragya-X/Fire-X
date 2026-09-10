"""Classification orchestration: temporal analysis -> features -> ML -> risk."""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.gis.engine import SpatialDataset, compute_infrastructure_features
from app.ml.features import build_feature_vector
from app.ml.predict import classify_vector
from app.models import (
    HistoricalDetection,
    Hotspot,
    InfrastructureFeature,
    SatelliteValidation,
)
from app.services.risk_engine import compute_risk
from app.services.temporal import analyze_detections, historical_features
from app.utils.helpers import risk_level_for


def _nearest_industrial(ftr: InfrastructureFeature) -> float:
    dists = [
        ftr.nearest_refinery_distance,
        ftr.nearest_factory_distance,
        ftr.nearest_powerplant_distance,
        ftr.nearest_mine_distance,
    ]
    valid = [d for d in dists if d is not None and d >= 0]
    return min(valid) if valid else -1.0


def analyze_hotspot(
    db: Session,
    hotspot: Hotspot,
    dataset: Optional[SpatialDataset] = None,
    *,
    update: bool = True,
) -> dict[str, Any]:
    """Run the full intelligence pipeline on one hotspot and (optionally) persist it."""
    features = hotspot.features
    if features is None:
        features = InfrastructureFeature(hotspot_id=hotspot.id)
        if dataset is not None:
            ctx = compute_infrastructure_features(dataset, hotspot.latitude, hotspot.longitude)
            for k, v in ctx.items():
                setattr(features, k, v)
        db.add(features)
        db.flush()

    history = sorted(hotspot.history, key=lambda h: h.detection_time)
    # Include the current acquisition as the most recent detection
    all_times = [h.detection_time for h in history] + [hotspot.acquisition_time]
    temporal = analyze_detections(all_times, window_days=14, now=hotspot.acquisition_time)
    temporal.update(historical_features(
        [h.to_dict() for h in history], reference_time=hotspot.acquisition_time,
        current_frp=hotspot.frp,
    ))

    # Query the latest validation from the DB (relationships may be stale)
    validation = (
        db.query(SatelliteValidation)
        .filter(SatelliteValidation.hotspot_id == hotspot.id)
        .order_by(SatelliteValidation.id.desc())
        .first()
    )

    vector = build_feature_vector(
        brightness=hotspot.brightness,
        frp=hotspot.frp,
        n_detections=temporal["n_detections"],
        persistence_score=temporal["persistence_score"],
        dist_industrial_km=_nearest_industrial(features),
        dist_forest_km=features.nearest_forest_distance,
        dist_agriculture_km=features.nearest_agriculture_distance,
        dist_settlement_km=features.nearest_settlement_distance,
        land_cover=hotspot.land_cover or "Other",
        acquisition_time=hotspot.acquisition_time,
        historical_frequency=temporal["n_detections"] / 14.0,
        validation_status=validation.status if validation else None,
    )

    prediction = classify_vector(
        vector,
        temporal_pattern=temporal["pattern"],
        satellite_validation=validation.status if validation else None,
    )

    risk = compute_risk(
        brightness=hotspot.brightness,
        frp=hotspot.frp,
        persistence_score=temporal["persistence_score"],
        temporal_pattern=temporal["pattern"],
        classification=prediction["classification"],
        nearest_industrial_km=_nearest_industrial(features),
        nearest_settlement_km=features.nearest_settlement_distance,
        nearest_forest_km=features.nearest_forest_distance,
        nearest_agriculture_km=features.nearest_agriculture_distance,
        satellite_status=validation.status if validation else None,
        n_history=temporal["n_detections"],
    )

    result = {
        "hotspot_id": hotspot.id,
        "hotspot_code": hotspot.code,
        "classification": prediction["classification"],
        "confidence": prediction["confidence"],
        "probabilities": prediction["probabilities"],
        "baseline": prediction["baseline"],
        **{k: prediction[k] for k in ("model_mode", "model_version", "training_data_type", "requested_mode", "fallback_reason")},
        "explanation": prediction["explanation"],
        "feature_vector": [round(v, 4) for v in vector],
        "temporal": temporal,
        "risk": risk,
    }

    if update:
        hotspot.classification = prediction["classification"]
        hotspot.classification_confidence = prediction["confidence"]
        hotspot.probabilities = prediction["probabilities"]
        hotspot.explanation = prediction["explanation"]
        hotspot.feature_vector = [round(v, 4) for v in vector]
        hotspot.persistence_score = temporal["persistence_score"]
        hotspot.temporal_pattern = temporal["pattern"]
        hotspot.risk_score = risk["score"]
        hotspot.risk_level = risk["level"]
        db.add(hotspot)
        db.flush()

    return result


def refresh_all(db: Session, dataset: Optional[SpatialDataset] = None) -> dict:
    """Re-run classification and risk for every hotspot."""
    hotspots = db.query(Hotspot).all()
    updated = 0
    for hs in hotspots:
        analyze_hotspot(db, hs, dataset)
        updated += 1
    db.commit()
    return {"updated": updated, "temporal_patterns": _pattern_counts(db)}


def _pattern_counts(db: Session) -> dict:
    from sqlalchemy import func

    rows = db.query(Hotspot.temporal_pattern, func.count()).group_by(Hotspot.temporal_pattern).all()
    return {k: v for k, v in rows}