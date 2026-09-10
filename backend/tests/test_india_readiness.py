"""Synthetic fixtures exercise data tooling only; never create project labels/models."""
import json
from pathlib import Path
import pandas as pd
import pytest
from shapely.geometry import box, mapping
from pyproj import Transformer
from app.ml.data.preprocessing import preprocess
from app.ml.data.preprocessing import normalize_firms
from app.ml.reference_bundle import load_reference_bundle, ReferenceBundleError
from app.ml.build_dataset import build_files
from app.ml.readiness import generate_report, history_diagnostics, feature_coverage, clustering_audit
from app.ml.spatial_features import event_spatial_features
from app.providers.osm import reference_features


def observation(day=1, latitude=22, longitude=70, frp=10):
    return dict(latitude=latitude,longitude=longitude,acq_date=f'2026-01-{day:02d}',
                acq_time='1200',frp=frp,brightness=330,satellite='test',instrument='VIIRS',daynight='D')


def feature(fid,category,geometry):
    return {'type':'Feature','id':fid,'properties':{'category':category},'geometry':geometry}


def write_geojson(path, features, **extra):
    path.write_text(json.dumps({'type':'FeatureCollection','features':features,**extra}))
    return path


def bundle(tmp_path):
    industrial=write_geojson(tmp_path/'industrial.geojson',[
        feature('way/1','factory',mapping(box(69.999,21.999,70.001,22.001))),
        feature('node/2','oil_gas',{'type':'Point','coordinates':[70.01,22]})])
    land=write_geojson(tmp_path/'land.geojson',[feature('land/1','forest',mapping(box(69.8,21.8,70.2,22.2)))],
        available_categories=['forest','agriculture','urban','industrial'],
        coverage={cat:mapping(box(69,21,71,23)) for cat in ('forest','agriculture','urban','industrial')})
    path=tmp_path/'bundle.json'
    path.write_text(json.dumps({'version':1,'layers':[
        {'name':'facilities','role':'industrial','path':industrial.name,'source':'synthetic-test industrial','version':'test-v1','crs':'EPSG:4326'},
        {'name':'land','role':'landcover','path':land.name,'source':'synthetic-test land','version':'test-v1','crs':'EPSG:4326'}]}))
    return path


def build_test_data(tmp_path, with_references=True):
    raw=tmp_path/'firms.csv'
    pd.DataFrame([observation(1,frp=10),observation(4,frp=20),observation(7,frp=30)]).to_csv(raw,index=False)
    clean=tmp_path/'clean.parquet'
    preprocess(raw,clean,tmp_path/'raw','synthetic-test',region='india')
    events=tmp_path/'events.parquet'
    build_files(clean,events,reference_bundle=bundle(tmp_path) if with_references else None)
    return clean,events


def test_india_multifile_metadata_and_dedupe(tmp_path):
    a,b=tmp_path/'a.csv',tmp_path/'b.parquet'
    pd.DataFrame([observation(1),observation(2)]).to_csv(a,index=False)
    pd.DataFrame([observation(2),observation(3,latitude=None)]).to_parquet(b,index=False)
    output=tmp_path/'clean.parquet'
    report=preprocess([b,a],output,tmp_path/'raw','synthetic-test',region='india')
    assert report['raw_row_count']==4 and report['valid_row_count']==2
    assert report['duplicate_count']==1 and report['missing_coordinate_count']==1
    assert report['outside_india_envelope_count']==0 and report['processing_timestamp']
    assert report['date_range']['start'].startswith('2026-01-01')
    assert report['geographic_bounds']['west']==70
    assert len(report['inputs'])==2 and all(item['sha256'] for item in report['inputs'])
    assert all('input_file' in issue for issue in report['issues'])
    first=pd.read_parquet(output)
    preprocess([a,b],output,tmp_path/'raw','synthetic-test',region='india')
    pd.testing.assert_frame_equal(first,pd.read_parquet(output))


def test_each_input_schema_validated(tmp_path):
    a,b=tmp_path/'a.csv',tmp_path/'b.csv'
    pd.DataFrame([observation()]).to_csv(a,index=False)
    pd.DataFrame([{'latitude':22,'longitude':70}]).to_csv(b,index=False)
    output=tmp_path/'clean.parquet'
    with pytest.raises(ValueError,match='Missing required schema'):
        preprocess([a,b],output,tmp_path/'raw','synthetic-test')
    assert not output.exists()
    report=json.loads(output.with_suffix('.validation.json').read_text())
    assert report['input_schema_errors'][0]['path']==str(b.resolve())


def test_bundle_provenance_and_geometry(tmp_path):
    path=bundle(tmp_path)
    dataset,meta=load_reference_bundle(path)
    features=event_spatial_features(dataset,22,70)
    assert features['dist_factory_km']==0 and features['forest_fraction_1km']>0.99
    assert dataset.points('oil_gas')[0].id=='node/2'
    assert dataset.points('factory')[0].meta['source']=='synthetic-test industrial'
    assert meta['industrial_reference_version']=='test-v1' and meta['landcover_source']
    old_hash=meta['reference_sha256']
    land=tmp_path/'land.geojson'; contents=json.loads(land.read_text()); contents['features'][0]['properties']['name']='changed'
    land.write_text(json.dumps(contents))
    assert load_reference_bundle(path)[1]['reference_sha256']!=old_hash


def test_bundle_projected_crs_and_class_mapping(tmp_path):
    x,y=Transformer.from_crs(4326,3857,always_xy=True).transform(70,22)
    geom={'type':'Point','coordinates':[x,y]}
    ref=write_geojson(tmp_path/'ref.geojson',[{'type':'Feature','properties':{'facility_id':'known/1','kind':'explicit_factory'},'geometry':geom}])
    config=tmp_path/'bundle.json'
    config.write_text(json.dumps({'version':1,'layers':[{'name':'i','role':'industrial','path':ref.name,'source':'synthetic-test','version':'1','crs':'EPSG:3857','category_property':'kind','category_map':{'explicit_factory':'factory'}}]}))
    dataset,_=load_reference_bundle(config)
    assert dataset.nearest_point('factory',22,70)['distance_km']<.001


def test_osm_export_never_guesses_unknown_type():
    exported,report=reference_features({'elements':[
        {'type':'node','id':1,'lat':0,'lon':0,'tags':{'industrial':'factory'}},
        {'type':'node','id':2,'lat':22,'lon':70,'tags':{'industrial':'unknown'}},
        {'type':'way','id':3,'center':{'lat':22,'lon':70},'tags':{'landuse':'industrial'}}]})
    assert len(exported['features'])==2 and len(report['rejected_features'])==1
    assert exported['features'][0]['geometry']['coordinates']==[0,0]
    assert exported['features'][1]['properties']['geometry_representation']=='center_only'
    assert exported['features'][0]['properties']['tags']['industrial']=='factory'


def test_invalid_reference_reports_rejection(tmp_path):
    path=bundle(tmp_path)
    industrial=tmp_path/'industrial.geojson'; doc=json.loads(industrial.read_text()); doc['features'][0]['properties']['category']='mystery'
    industrial.write_text(json.dumps(doc))
    with pytest.raises(ReferenceBundleError) as error: load_reference_bundle(path)
    assert error.value.report['layers'][0]['rejected_features'][0]['reason']=='UNKNOWN_OR_WRONG_ROLE_CATEGORY'


def test_report_coverage_inspection_and_blocked_state(tmp_path):
    clean,events=build_test_data(tmp_path)
    report=generate_report(events,clean,tmp_path/'validation',tmp_path/'inspection',sample_size=2)
    assert report['status']=='VALIDATED_UNREVIEWED'
    assert report['training_ready'] is False and report['event_count']==3
    assert report['industrial_context_coverage']['dist_factory_km']['non_null']==3
    assert report['landcover_context_coverage']['forest_fraction_1km']['null']==0
    assert report['temporal_context_coverage']['historical_mean_frp']['non_null']==2
    assert report['readiness']['DATA_PIPELINE_READY']['ready'] is True
    assert report['readiness']['REFERENCE_COVERAGE_READY']['ready'] is False
    assert len(pd.read_csv(tmp_path/'inspection.csv'))==2
    assert 'Member detections' in (tmp_path/'inspection.md').read_text()
    assert report['history_reason_counts']['NO_PRIOR_OBSERVATIONS']==1
    assert 'null_percentage' in report['feature_coverage']['mean_frp']


def test_missing_inputs_and_no_reference_behavior(tmp_path):
    report=generate_report(tmp_path/'missing.parquet',tmp_path/'missing_clean.parquet',tmp_path/'missing_report',tmp_path/'sample')
    assert report['event_count'] is None and report['status']=='MISSING_INPUTS'
    clean,events=build_test_data(tmp_path,False)
    report=generate_report(events,clean,tmp_path/'validation',tmp_path/'inspection')
    assert report['industrial_context_coverage']['dist_factory_km']['null_percentage']==100
    assert 'NO_REFERENCE_BUNDLE' in report['blockers']


def test_tampered_manifest_detected(tmp_path):
    clean,events=build_test_data(tmp_path)
    frame=pd.read_parquet(events); frame.loc[0,'mean_frp']=999
    frame.to_parquet(events,index=False)
    report=generate_report(events,clean,tmp_path/'validation',tmp_path/'inspection')
    assert report['status']=='INVALID_INPUTS' and report['training_ready'] is False
    assert any('sha256' in reason for reason in report['blockers'])


def test_history_reason_differences():
    clean=normalize_firms(pd.DataFrame([observation(1),observation(3,latitude=23),observation(5,frp=None)]))[0]
    events=pd.DataFrame([
        dict(event_id='none',start_time=pd.Timestamp('2026-01-01',tz='UTC'),centroid_latitude=22,centroid_longitude=70,mean_frp=10),
        dict(event_id='far',start_time=pd.Timestamp('2026-01-04',tz='UTC'),centroid_latitude=25,centroid_longitude=70,mean_frp=10),
        dict(event_id='one',start_time=pd.Timestamp('2026-01-04',tz='UTC'),centroid_latitude=22,centroid_longitude=70,mean_frp=10)])
    reasons=history_diagnostics(events,clean,1).set_index('event_id')
    assert reasons.loc['none','history_reason']=='NO_PRIOR_OBSERVATIONS'
    assert reasons.loc['far','history_reason']=='NO_MATCH_WITHIN_HISTORY_RADIUS'
    assert reasons.loc['one','history_reason']=='INSUFFICIENT_HISTORY'
    assert bool(reasons.loc['one','baseline_available'])


def test_landcover_industry_is_not_a_facility(tmp_path):
    land=write_geojson(tmp_path/'land.geojson',[feature('cell/1','industrial',mapping(box(69.9,21.9,70.1,22.1)))])
    config=tmp_path/'bundle.json'
    config.write_text(json.dumps({'version':1,'layers':[{'name':'land','role':'landcover','path':land.name,'source':'synthetic-test','version':'1','crs':'EPSG:4326'}]}))
    dataset,_=load_reference_bundle(config)
    context=event_spatial_features(dataset,22,70)
    assert context['dist_nearest_industrial_km']==0
    assert context['nearest_facility_id'] is None
    assert context['industrial_count_1km'] is None
    assert context['inside_industrial_polygon'] is True
    assert event_spatial_features(dataset,24,70)['inside_industrial_polygon'] is None


def test_reference_hash_change_blocks_report(tmp_path):
    clean,events=build_test_data(tmp_path)
    industrial=tmp_path/'industrial.geojson'
    data=json.loads(industrial.read_text()); data['features'][0]['properties']['name']='new version'
    industrial.write_text(json.dumps(data))
    report=generate_report(events,clean,tmp_path/'validation',tmp_path/'inspection')
    assert report['status']=='INVALID_INPUTS'
    assert any('Reference bundle/input hash mismatch' in reason for reason in report['blockers'])


def test_clustering_flags_do_not_change_parameters():
    events=pd.DataFrame([dict(event_id='review',spatial_radius_km=2,duration_minutes=1500)])
    # Two singleton endpoints would need coordinates; one event still builds the index.
    events['centroid_latitude']=22; events['centroid_longitude']=70
    report=clustering_audit(events,{'spatial_km':1,'temporal_hours':24})
    assert report['event_flags'][0]['reasons']==['SPATIAL_CHAIN_REVIEW','TEMPORAL_CHAIN_REVIEW']
    assert report['parameters']=={'spatial_km':1,'temporal_hours':24}
    assert report['parameter_change_recommendation'] is None
