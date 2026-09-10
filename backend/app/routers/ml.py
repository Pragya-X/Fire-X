from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_role
from app.ml.predict import classification_health, classify_vector, model_available, load_model
from app.models import ActivityLog, Hotspot, User
from app.schemas import ClassifyRequest, ClassificationOut
from app.services.classification_service import analyze_hotspot

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])


@router.post("/classify", response_model=ClassificationOut)
def classify(body: ClassifyRequest, db: Session = Depends(get_db), user: User = Depends(require_role("analyst"))):
    h = db.get(Hotspot, body.hotspot_id)
    if h is None:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    result = analyze_hotspot(db, h, update=True)
    db.add(ActivityLog(user=user.email, action="classification", entity="hotspot", entity_id=h.code))
    db.commit()
    return ClassificationOut(
        **{k: result[k] for k in ("model_mode", "model_version", "training_data_type", "requested_mode", "fallback_reason")},
        feature_importance_type="global_model_importance" if getattr(load_model(), "feature_importances_", None) is not None else "heuristic_weights",
        hotspot_id=h.id,
        hotspot_code=h.code,
        classification=result["classification"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        feature_importance=_importance(),
        risk_score=result["risk"]["score"],
        risk_level=result["risk"]["level"],
        explanation=result["explanation"],
    )


def _importance() -> dict:
    """Feature importance from the trained model, or heuristic weights."""
    from app.ml.predict import load_model
    from app.ml.features import FEATURE_NAMES
    model = load_model()
    importances = getattr(model, "feature_importances_", None)
    if importances is not None:
        return {name: round(float(v), 4) for name, v in zip(FEATURE_NAMES, importances)}
    heuristic = [0.12, 0.10, 0.08, 0.10, 0.12, 0.08, 0.08, 0.07, 0.08, 0.03, 0.05, 0.06, 0.02, 0.01]
    return {name: round(float(v), 4) for name, v in zip(FEATURE_NAMES, heuristic)}


@router.get("/status")
def ml_status():
    health = classification_health()
    return {"online": model_available(), **health}