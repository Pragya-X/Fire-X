from datetime import timedelta
from app.services.temporal import historical_features, analyze_detections
from test_temporal import NOW


def test_history_excludes_future_and_current():
    records=[dict(acquisition_time=NOW+timedelta(days=d),frp=f,brightness=330,latitude=0,longitude=0,daynight='N') for d,f in [(-2,10),(-1,20),(0,999),(1,999)]]
    r=historical_features(records,reference_time=NOW,current_frp=30,latitude=0,longitude=0)
    assert r['detections_7d']==2 and r['historical_mean_frp']==15
    assert r['frp_z_score']==3 and r['time_since_previous_detection']==24
    assert r['active_days_7d']==2 and r['spatial_location_variance']==0


def test_empty_single_and_zero_variance():
    assert historical_features([],reference_time=NOW)['historical_mean_frp'] is None
    record=dict(acquisition_time=NOW-timedelta(days=1),frp=0)
    r=historical_features([record,record],reference_time=NOW,current_frp=30)
    assert r['detections_7d']==1
    assert r['frp_z_score'] is None and r['frp_ratio_to_baseline'] is None
    assert r['mean_detection_interval_hours'] is None


def test_space_and_90d_window():
    records=[dict(acquisition_time=NOW-timedelta(days=d),frp=5,latitude=lat,longitude=0) for d,lat in [(1,10),(91,0),(2,0)]]
    r=historical_features(records,reference_time=NOW,latitude=0,longitude=0)
    assert r['detections_90d']==1


def test_legacy_window_and_burst_score():
    r=analyze_detections([NOW-timedelta(days=20),NOW+timedelta(days=1),NOW],now=NOW)
    assert r['n_detections']==1
    burst=analyze_detections([NOW-timedelta(minutes=i) for i in range(100)],now=NOW)
    assert burst['persistence_score']<50
