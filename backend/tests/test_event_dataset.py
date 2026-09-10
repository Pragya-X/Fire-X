import pandas as pd
import pytest
from app.ml.build_dataset import build_event_dataset, build_files
from app.ml.datasets import COLUMNS
from test_event_clustering import detections


def clean():
    df=detections(); df['data_source']='synthetic-test'
    return df


def test_dataset_unlabeled_history_and_missing_context():
    events,members,report=build_event_dataset(clean())
    assert list(events)==COLUMNS and len(events)==2
    assert len(members)==3 and report['detection_count']==3
    assert events.iloc[0].detections_90d==0
    assert events.iloc[1].historical_mean_frp==15
    assert events.dist_nearest_industrial_km.isna().all()
    assert report['training_ready'] is False
    assert 'label' not in events


def test_dataset_reproducible_files(tmp_path):
    source=tmp_path/'clean.parquet'; clean().to_parquet(source,index=False)
    a,b=tmp_path/'a.parquet',tmp_path/'b.parquet'
    assert build_files(source,a)==build_files(source,b)
    pd.testing.assert_frame_equal(pd.read_parquet(a),pd.read_parquet(b))
    assert a.with_suffix('.membership.parquet').exists()
    assert a.with_suffix('.schema.json').exists()


def test_empty_schema_and_unvalidated_input():
    events,_,report=build_event_dataset(clean().iloc[:0])
    assert list(events)==COLUMNS and report['event_count']==0
    with pytest.raises(ValueError): build_event_dataset(detections())
    df=clean();df.loc[0,'frp']=-1
    with pytest.raises(ValueError): build_event_dataset(df)


def test_long_current_event_has_persistence_without_baseline_leakage():
    from app.ml.data.preprocessing import normalize_firms
    observations=pd.DataFrame([dict(latitude=22,longitude=70,acq_date=f'2026-01-{d:02d}',acq_time='1200',frp=10,brightness=330,daynight='D') for d in range(1,11)])
    frame=normalize_firms(observations)[0]; frame['data_source']='synthetic-test'
    events,_,_=build_event_dataset(frame)
    assert len(events)==1 and events.iloc[0].persistence_score>=50
    assert pd.isna(events.iloc[0].historical_mean_frp)
