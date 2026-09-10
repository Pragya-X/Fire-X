from app.gis.engine import SpatialDataset, compute_infrastructure_features, haversine_km
from app.seed_data import build_dataset


def test_haversine_known_distance():
    # Delhi -> Agra ~190 km
    d = haversine_km(28.61, 77.21, 27.18, 78.01)
    assert 170 < d < 210


def test_dataset_nearest_point():
    ds = build_dataset()
    nearest = ds.nearest_point("refinery", 22.26, 69.79)
    assert nearest is not None
    assert nearest["distance_km"] < 5.0
    assert "Jamnagar" in nearest["name"] or "Vadinar" in nearest["name"]


def test_infrastructure_features_shape():
    ds = build_dataset()
    feats = compute_infrastructure_features(ds, 22.26, 69.79)
    for key in (
        "nearest_refinery_distance", "nearest_factory_distance", "nearest_powerplant_distance",
        "nearest_mine_distance", "nearest_forest_distance", "nearest_agriculture_distance",
        "nearest_settlement_distance", "nearest_road_distance", "nearest_railway_distance",
        "nearest_pipeline_distance",
    ):
        assert key in feats
        assert feats[key] >= 0


def test_land_cover_industrial_near_zone():
    ds = build_dataset()
    lc = ds.land_cover(22.26, 69.79)  # inside Jamnagar refinery complex
    assert lc == "Industrial"