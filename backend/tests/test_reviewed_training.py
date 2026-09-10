"""Scientific guard tests use explicitly synthetic unit fixtures, never project labels."""
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from app.ml.labels import Annotation,validate_annotations
from app.ml.splits import SplitConfig,make_splits,leakage_groups
from app.ml.training import prepare,train,FEATURES
from app.ml.evaluation import evaluate
from app.services.event_intelligence import hybrid_decision,statistical_anomaly,HistoricalAnomalyModel


def annotation(**overrides):
    return dict(event_id='unit-event',label='Industrial Fire',review_status='approved',annotator='author',reviewer='reviewer',
                confidence=.9,quality='A',source='UNIT FIXTURE ONLY',evidence=['unit://test-evidence'],
                reviewed_at='2025-01-01T00:00:00Z',**overrides)


def test_label_independent_review_and_unknown():
    data=annotation();assert Annotation(**data).training_eligible
    data['reviewer']='author'
    with pytest.raises(ValueError,match='different reviewer'): Annotation(**data)
    data=annotation();data['label']='Unknown'
    assert not Annotation(**data).training_eligible
    data['label']='Industrial Fire';data['quality']='C'
    assert not Annotation(**data).training_eligible

@pytest.mark.parametrize('field,value',[('confidence',None),('reviewed_at',None),('reviewed_at','2025-01-01'),('evidence',[]),('source',''),('label','fabricated-class')])
def test_invalid_approved_annotations(field,value):
    data=annotation();data[field]=value
    with pytest.raises(ValueError): Annotation(**data)


def test_label_duplicates_and_unknown_ids():
    _,report=validate_annotations([annotation(),annotation()],{'unit-event'})
    assert not report['valid']
    _,report=validate_annotations([annotation()],set())
    assert not report['valid']


def split_frame():
    return pd.DataFrame({'event_id':[f'unit-{i}' for i in range(15)],
        'centroid_latitude':[8.0+i for i in range(15)],'centroid_longitude':[75]*15,
        'nearest_facility_id':[None]*15,'start_time':pd.to_datetime(['2024-01-01']*15,utc=True),
        'end_time':pd.to_datetime(['2024-01-02']*15,utc=True),'label':['Other']*15})


def test_geographic_split_distance_chain_facility_and_determinism():
    frame=split_frame();frame.loc[1,'centroid_latitude']=8.01
    frame.loc[2,'centroid_latitude']=8.02
    frame.loc[[2,10],'nearest_facility_id']='same-facility'
    groups=leakage_groups(frame,2)
    assert groups[0]==groups[1]==groups[2]==groups[10]
    a,report=make_splits(frame,SplitConfig(radius_km=2));b,_=make_splits(frame,SplitConfig(radius_km=2))
    assert a.equals(b) and report['valid']
    assert a.loc[[0,1,2,10],'split'].nunique()==1
    shuffled=frame.sample(frac=1,random_state=5)
    c,_=make_splits(shuffled,SplitConfig(radius_km=2))
    assert a.set_index('event_id').sort_index().equals(c.set_index('event_id').sort_index())


def test_temporal_purge_and_shared_facility():
    frame=split_frame()
    frame['start_time']=pd.to_datetime(['2023-01-01']*5+['2024-05-01']*5+['2025-05-01']*5,utc=True)
    frame['end_time']=frame.start_time+pd.Timedelta(hours=2)
    frame.loc[[0,5],'nearest_facility_id']='cross-boundary'
    frame.loc[11,'start_time']=pd.Timestamp('2025-01-02',tz='UTC');frame.loc[11,'end_time']=frame.loc[11,'start_time']
    assignments,report=make_splits(frame,SplitConfig(strategy='temporal',train_end='2024-01-01T00:00Z',validation_end='2025-01-01T00:00Z'))
    assert assignments.loc[[0,5,11],'split'].tolist()==['excluded']*3
    assert report['valid'] and report['counts']=={'train':4,'validation':4,'test':4}


def test_split_rejects_duplicates_missing_facility_and_empty():
    frame=split_frame();frame.loc[1,'event_id']=frame.loc[0,'event_id']
    with pytest.raises(ValueError,match='Duplicate'): make_splits(frame,SplitConfig())
    with pytest.raises(ValueError,match='verified facility'): make_splits(split_frame(),SplitConfig(strategy='facility'))
    with pytest.raises(ValueError): SplitConfig(history_days=1)


def test_identity_and_rule_outputs_not_features():
    assert not {'event_id','nearest_facility_id','start_time','persistence_score','centroid_latitude','label'}.intersection(FEATURES)


def test_blocked_training_never_fits(tmp_path,monkeypatch):
    path=tmp_path/'training_dataset.parquet';pd.DataFrame().to_parquet(path)
    (tmp_path/'training_manifest.json').write_text(json.dumps({'training_ready':False,'blockers':['NO_LABELS']}))
    from sklearn.linear_model import LogisticRegression
    monkeypatch.setattr(LogisticRegression,'fit',lambda *a,**kw:pytest.fail('fit must never run'))
    with pytest.raises(ValueError,match='TRAINING BLOCKED'): train(path,tmp_path/'models')
    assert not (tmp_path/'models').exists()
    with pytest.raises(ValueError,match='TRAINING BLOCKED'): HistoricalAnomalyModel().fit_reviewed(path,['fake']*30)


def test_metric_values_are_computed_and_absent_class_is_unavailable():
    result=evaluate(['A','A','B','B'],[[.9,.1],[.6,.4],[.2,.8],[.7,.3]],['A','B'])
    assert result['accuracy']==.75 and result['confusion_matrix']==[[2,0],[1,1]]
    assert sum(b['count'] for b in result['per_class']['A']['reliability'])==4
    missing=evaluate(['A','A'],[[.9,.1],[.6,.4]],['A','B'])
    assert missing['per_class']['B']['available'] is False
    with pytest.raises(ValueError): evaluate(['A'],[[.2,.2]],['A','B'])


def test_anomaly_no_baseline_and_zero_variance_are_unknown():
    assert statistical_anomaly({'mean_frp':100})['score'] is None
    assert statistical_anomaly({'mean_frp':100,'historical_mean_frp':10,'historical_std_frp':0,'detections_90d':90})['score'] is None
    event={'mean_frp':40,'historical_mean_frp':10,'historical_std_frp':5,'detections_90d':90,'active_days_90d':60,'inside_industrial_polygon':True}
    result=hybrid_decision(event)
    assert result['decision']=='Unknown' and result['confidence'] is None
    assert result['anomaly']['score']==6 and result['risk']['priority']=='review'
    assert result['persistence']['status']=='persistent_candidate'
    result=hybrid_decision(event,{'mode':'trained','probabilities':{'Other':.2,'Industrial Fire':.8}})
    assert result['decision']=='Industrial Fire' and result['confidence']==.8


def test_prepare_empty_labels_produces_blocked_auditable_dataset(tmp_path):
    from app.ml.data.preprocessing import preprocess
    from app.ml.build_dataset import build_files
    source=Path(__file__).resolve().parents[2]/'data'/'samples'/'firms_nasa_tutorial.csv'
    clean=tmp_path/'clean.parquet';events=tmp_path/'events.parquet'
    preprocess(source,clean,tmp_path/'raw',source='NASA tutorial test excerpt')
    build_files(clean,events)
    result=prepare(events,tmp_path/'missing-labels.json',tmp_path/'missing-readiness.json',tmp_path/'prepared')
    assert result['training_ready'] is False and result['class_distribution']=={}
    assert 'NO_REFERENCE_BUNDLE' in result['blockers']
    assert pd.read_parquet(tmp_path/'prepared'/'training_dataset.parquet').empty
    assert (tmp_path/'prepared'/'feature_manifest.json').exists()
    with pytest.raises(ValueError,match='TRAINING BLOCKED'): train(tmp_path/'prepared'/'training_dataset.parquet',tmp_path/'model')


def test_reliability_bins_cover_extremes_and_edges():
    probabilities=np.arange(11)/10
    result=evaluate(['A' if i%2 else 'B' for i in range(11)],np.column_stack([probabilities,1-probabilities]),['A','B'])
    for metrics in result['per_class'].values(): assert sum(b['count'] for b in metrics['reliability'])==11


def test_event_model_never_loads_unapproved_artifact(tmp_path,monkeypatch):
    from app.config import settings
    from app.services.event_intelligence import load_approved_model,predict_event
    import joblib
    artifact=tmp_path/'unit.joblib';artifact.write_bytes(b'not a model')
    monkeypatch.setattr(settings,'MODEL_DIR',str(tmp_path))
    monkeypatch.setattr(settings,'EVENT_MODEL_PATH',str(artifact))
    monkeypatch.setattr(joblib,'load',lambda *a:pytest.fail('Unapproved artifacts must never deserialize'))
    model,reason=load_approved_model()
    assert model is None and reason
    assert predict_event({'mean_frp':10})['decision']=='Unknown'
    monkeypatch.setattr(settings,'EVENT_MODEL_PATH','/tmp/outside-unit.joblib')
    assert 'inside MODEL_DIR' in load_approved_model()[1]


def test_normal_operation_requires_independent_hash_bound_review():
    from app.ml.normal_reviews import validate_normal_reviews
    document={'dataset_sha256':'unit-hash','reviews':[{'event_id':'unit','normal_operation':True,'annotator':'author','reviewer':'reviewer',
        'source':'UNIT ONLY','evidence':['unit://evidence'],'reviewed_at':'2025-01-01T00:00:00Z'}]}
    assert validate_normal_reviews(document,'unit-hash')==['unit']
    with pytest.raises(ValueError):validate_normal_reviews(document,'changed-hash')
    document['reviews'][0]['reviewer']='author'
    with pytest.raises(ValueError):validate_normal_reviews(document,'unit-hash')


def test_spatial_groups_account_for_chained_event_footprints():
    frame=split_frame().iloc[:3].copy()
    frame['centroid_latitude']=[22,22.1,24]
    frame['spatial_radius_km']=[7,7,0]
    groups=leakage_groups(frame,2)
    assert groups[0]==groups[1] and groups[1]!=groups[2]


def test_empty_review_template_reports_blockers(tmp_path):
    from app.ml.training import assess_inputs
    events=tmp_path/'events.parquet';pd.DataFrame().to_parquet(events)
    reviews=tmp_path/'reviews.json'
    reviews.write_text(json.dumps({'representativeness':{'approved':False,'reviewer':'','reviewed_at':None,'evidence':[]}}))
    reasons=assess_inputs(events,tmp_path/'missing-report.json',reviews)
    assert 'REPRESENTATIVENESS_NOT_REVIEWED' in reasons
