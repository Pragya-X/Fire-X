"""Train the FIRE-X baseline classifier.

Generates synthetic (but realistic) training data from the same feature
distributions the demo seed data uses, trains a HistGradientBoosting classifier
(and XGBoost when installed), evaluates on a holdout split and writes:

    ml/models/model.pkl
    ml/models/metrics.json

Run from the backend directory:

    python -m app.ml.train_model
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from app.config import settings
from app.ml.features import CLASSES, FEATURE_NAMES, LAND_COVER_CODES, land_cover_code

OUT_MODEL = Path(settings.MODEL_DIR) / "model.pkl"
OUT_METRICS = Path(settings.MODEL_DIR) / "metrics.json"

N_SAMPLES = 2400
SEED = 7


def _sample_labeled_sample(rng: random.Random) -> tuple[list[float], str]:
    """Draw one (feature vector, label) from the same distributions as seed data.

    Labels are assigned by the same logic as the baseline rule engine, so the
    trained model reproduces the demo behaviour while learning real decision
    boundaries from noisy data.
    """
    kind = rng.random()
    land_cover = "Industrial"
    d_ind, d_for, d_agr, d_set = 0.5, 20.0, 12.0, 4.0
    n_det, persistence, temporal = 1, 5.0, "sudden"
    brightness, frp = rng.uniform(300, 420), rng.uniform(0.5, 160)
    tod = rng.uniform(0.2, 1.0)

    if kind < 0.42:  # industrial
        land_cover = "Industrial"
        d_ind = rng.uniform(0.1, 5.0)
        d_for, d_agr, d_set = rng.uniform(4, 30), rng.uniform(3, 25), rng.uniform(1, 12)
        p = rng.random()
        if p < 0.55:
            n_det = rng.randint(6, 12)
            persistence = rng.uniform(55, 95)
            temporal = "persistent"
            brightness = rng.uniform(325, 400)
            frp = rng.uniform(15, 110)
        elif p < 0.8:
            n_det = rng.randint(1, 2)
            persistence = rng.uniform(0, 20)
            temporal = "sudden"
            brightness = rng.uniform(350, 425)
            frp = rng.uniform(40, 160)
        else:
            n_det = rng.randint(4, 8)
            persistence = rng.uniform(25, 60)
            temporal = "recurring"
            brightness = rng.uniform(330, 390)
            frp = rng.uniform(15, 80)
    elif kind < 0.67:  # agriculture
        land_cover = "Agriculture"
        d_agr = rng.uniform(0.1, 2.0)
        d_ind = rng.uniform(8, 60)
        d_for = rng.uniform(10, 60)
        d_set = rng.uniform(1, 15)
        n_det = rng.randint(1, 4)
        persistence = rng.uniform(0, 40)
        temporal = rng.choice(["sudden", "intermittent", "recurring"])
        brightness = rng.uniform(300, 348)
        frp = rng.uniform(2, 25)
        tod = rng.uniform(0.55, 1.0)
    elif kind < 0.87:  # wildfire
        land_cover = "Forest"
        d_for = rng.uniform(0.0, 2.0)
        d_ind = rng.uniform(15, 80)
        d_agr = rng.uniform(8, 50)
        d_set = rng.uniform(3, 25)
        n_det = rng.randint(2, 8)
        persistence = rng.uniform(15, 70)
        temporal = rng.choice(["sudden", "recurring", "intermittent"])
        brightness = rng.uniform(305, 365)
        frp = rng.uniform(8, 70)
    else:  # other / flare-ish anomalies
        land_cover = rng.choice(["Barren", "Other", "Urban"])
        d_ind = rng.uniform(0.2, 30)
        d_for = rng.uniform(3, 40)
        d_agr = rng.uniform(3, 30)
        d_set = rng.uniform(0.5, 10)
        n_det = rng.randint(1, 6)
        persistence = rng.uniform(0, 80)
        temporal = rng.choice(["unknown", "intermittent", "persistent"])
        brightness = rng.uniform(295, 330)
        frp = rng.uniform(0.5, 12)

    # Gas flares - bright persistent sources very close to refineries/power
    if rng.random() < 0.08 and land_cover == "Industrial" and d_ind < 1.0:
        n_det = rng.randint(8, 14)
        persistence = rng.uniform(70, 98)
        brightness = rng.uniform(365, 420)
        frp = rng.uniform(80, 180)
        temporal = "persistent"

    vector = [
        brightness,
        frp,
        float(n_det),
        persistence,
        d_ind,
        d_for,
        d_agr,
        d_set,
        land_cover_code(land_cover),
        tod,
        n_det / 14.0,
        rng.choice([0.0, 0.0, 1.0, 2.0, 3.0]),
        frp / 160.0,
        (brightness - 300.0) / 120.0,
    ]

    label = _label_from_vector(vector)
    # Small label noise keeps the model honest
    if rng.random() < 0.04:
        label = rng.choice(CLASSES)
    return vector, label


def _label_from_vector(vector: list[float]) -> str:
    from app.ml.predict import rule_scores

    scores = rule_scores(vector)
    return max(scores, key=scores.get)


def main() -> None:
    rng = random.Random(SEED)
    X, y = [], []
    while len(X) < N_SAMPLES:
        vec, label = _sample_labeled_sample(rng)
        if label is None:
            continue
        X.append(vec)
        y.append(label)

    X = np.array(X)
    y = np.array(y)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)

    # Use Histogram-based Gradient Boosting instead of heavy iterative Random Forests
    model = HistGradientBoostingClassifier(max_iter=200, max_depth=14, min_samples_leaf=3, random_state=SEED)
    model.fit(Xtr, ytr)

    acc = accuracy_score(yte, model.predict(Xte))
    report = classification_report(yte, model.predict(Xte), output_dict=True, zero_division=0)

    metrics = {
        "model": "HistGradientBoosting",
        "n_samples": N_SAMPLES,
        "test_accuracy": round(acc, 4),
        "classification_report": {k: v for k, v in report.items() if isinstance(v, dict)},
        "note": "Trained on synthetic baseline data - demonstration model, not a production evaluation.",
    }
    print(f"Trained HistGradientBoosting - test accuracy {acc:.4f}")

    # Optional XGBoost upgrade
    try:
        from xgboost import XGBClassifier

        xgb = XGBClassifier(n_estimators=150, max_depth=8, random_state=SEED, eval_metric="mlogloss")
        xgb.fit(Xtr, ytr)
        xacc = accuracy_score(yte, xgb.predict(Xte))
        print(f"XGBoost available - test accuracy {xacc:.4f}")
        model = xgb
        metrics["model"] = "XGBoost"
        metrics["test_accuracy"] = round(xacc, 4)
    except Exception:
        print("XGBoost not installed - using RandomForest")

    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUT_MODEL)
    OUT_METRICS.write_text(json.dumps(metrics, indent=2))
    (OUT_MODEL.parent / "demo_metadata.json").write_text(json.dumps({
        "model_version": "synthetic-demo-v1", "training_data_type": "synthetic",
        "feature_names": FEATURE_NAMES, "model_mode": "DEMO_MODEL",
    }, indent=2))
    print(f"Model written to {OUT_MODEL}")
    print(f"Metrics written to {OUT_METRICS}")


if __name__ == "__main__":
    main()