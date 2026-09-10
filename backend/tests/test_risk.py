from app.services.risk_engine import compute_risk, risk_level_for


def test_risk_levels():
    assert risk_level_for(10) == "LOW"
    assert risk_level_for(30) == "MODERATE"
    assert risk_level_for(50) == "ELEVATED"
    assert risk_level_for(70) == "HIGH"
    assert risk_level_for(90) == "CRITICAL"


def test_hot_industrial_fire_is_critical():
    res = compute_risk(
        brightness=400.0, frp=120.0, persistence_score=40.0,
        temporal_pattern="sudden", classification="Industrial Fire",
        nearest_industrial_km=0.8, nearest_settlement_km=2.0,
        nearest_forest_km=20.0, nearest_agriculture_km=15.0,
        satellite_status="CONFIRMED", n_history=2,
    )
    assert res["score"] > 80
    assert res["level"] == "CRITICAL"
    assert "Immediate field verification" in res["recommendation"]


def test_low_intensity_detection_is_low_risk():
    res = compute_risk(
        brightness=305.0, frp=3.0, persistence_score=5.0,
        temporal_pattern="unknown", classification="Other Thermal Anomaly",
        nearest_industrial_km=60.0, nearest_settlement_km=40.0,
        nearest_forest_km=30.0, nearest_agriculture_km=2.0,
        satellite_status=None, n_history=1,
    )
    assert res["score"] < 40
    assert res["level"] in ("LOW", "MODERATE")


def test_trend_has_four_points():
    res = compute_risk(
        brightness=390.0, frp=90.0, persistence_score=30.0,
        temporal_pattern="sudden", classification="Industrial Fire",
        nearest_industrial_km=1.0, nearest_settlement_km=3.0,
        nearest_forest_km=18.0, nearest_agriculture_km=12.0,
        satellite_status="LIKELY", n_history=4,
    )
    assert len(res["trend"]) == 4
    assert res["trend"][-1] == res["score"]