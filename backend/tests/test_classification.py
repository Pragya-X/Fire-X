from app.ml.features import FEATURE_NAMES, build_feature_vector
from app.ml.predict import classify_vector, rule_classify


def _vec(**overrides):
    base = dict(
        brightness=320.0, frp=10.0, n_detections=2, persistence_score=10.0,
        dist_industrial_km=30.0, dist_forest_km=20.0, dist_agriculture_km=0.5,
        dist_settlement_km=5.0, land_cover="Agriculture",
        acquisition_time=None, historical_frequency=0.14, validation_status=None,
    )
    base.update(overrides)
    return build_feature_vector(**base)


def test_agricultural_burning():
    res = rule_classify(_vec())
    assert res["classification"] == "Agricultural Burning"
    assert res["confidence"] > 0.5


def test_persistent_industrial():
    res = rule_classify(
        _vec(
            brightness=350.0, frp=50.0, n_detections=9, persistence_score=80.0,
            dist_industrial_km=0.8, dist_agriculture_km=10.0, land_cover="Industrial",
        )
    )
    assert res["classification"] == "Persistent Industrial Heat Source"


def test_gas_flare():
    res = rule_classify(
        _vec(
            brightness=395.0, frp=150.0, n_detections=11, persistence_score=90.0,
            dist_industrial_km=0.4, dist_agriculture_km=15.0, land_cover="Industrial",
        )
    )
    assert res["classification"] == "Gas Flare"


def test_industrial_fire():
    res = rule_classify(
        _vec(
            brightness=380.0, frp=90.0, n_detections=2, persistence_score=10.0,
            dist_industrial_km=1.2, dist_agriculture_km=12.0, land_cover="Industrial",
        )
    )
    assert res["classification"] == "Industrial Fire"


def test_wildfire():
    res = rule_classify(
        _vec(
            brightness=335.0, frp=30.0, n_detections=4, persistence_score=40.0,
            dist_industrial_km=25.0, dist_forest_km=1.0, dist_agriculture_km=12.0,
            land_cover="Forest",
        )
    )
    assert res["classification"] == "Wildfire"


def test_other_anomaly_fallback():
    res = rule_classify(
        _vec(
            brightness=300.0, frp=1.0, n_detections=1, persistence_score=0.0,
            dist_industrial_km=120.0, dist_forest_km=100.0, dist_agriculture_km=90.0,
            land_cover="Barren",
        )
    )
    assert res["classification"] == "Other Thermal Anomaly"


def test_classify_vector_returns_explanation():
    res = classify_vector(
        _vec(),
        temporal_pattern="sudden",
        satellite_validation="LIKELY",
    )
    assert res["classification"] == "Agricultural Burning"
    assert "explanation" in res
    assert "model_derived_factors" in res["explanation"]
    assert "reasoning" in res["explanation"]
    assert len(res["probabilities"]) == 6