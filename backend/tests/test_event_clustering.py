import pandas as pd
import pytest
from app.ml.data.preprocessing import normalize_firms
from app.ml.build_dataset import cluster_events, ClusteringConfig


def detections():
    return normalize_firms(pd.DataFrame([
        dict(latitude=0,longitude=179.999,acq_date='2026-01-01',acq_time='0030',frp=10,brightness=330,daynight='N'),
        dict(latitude=0,longitude=-179.999,acq_date='2026-01-01',acq_time='0100',frp=20,brightness=340,daynight='D'),
        dict(latitude=0,longitude=179.999,acq_date='2026-01-03',acq_time='0100',frp=5,brightness=320,daynight='N'),
    ]))[0]


def test_space_time_and_dateline():
    events, assigned = cluster_events(detections())
    assert len(events)==2 and len(assigned)==3
    event = events.iloc[0]
    assert event.detection_count == 2 and event.mean_frp == 15
    assert abs(event.centroid_longitude)>179
    assert event.spatial_radius_km < .2
    assert event.duration_minutes == 30 and event.std_frp == 5


def test_deterministic_and_singleton():
    a,_ = cluster_events(detections())
    b,_ = cluster_events(detections().sample(frac=1,random_state=4))
    pd.testing.assert_frame_equal(a,b)
    assert a.iloc[1].duration_minutes == 0
    assert a.iloc[1].std_frp == 0


def test_invalid_and_empty():
    df=detections(); df.loc[0,'latitude']=91
    with pytest.raises(ValueError): cluster_events(df)
    assert cluster_events(detections().iloc[:0])[0].empty
    with pytest.raises(ValueError): ClusteringConfig(spatial_km=0)


def test_equivalent_numeric_configs_have_same_identity():
    a,_=cluster_events(detections(),ClusteringConfig(1,24))
    b,_=cluster_events(detections(),ClusteringConfig(1.0,24.0))
    pd.testing.assert_frame_equal(a,b)
