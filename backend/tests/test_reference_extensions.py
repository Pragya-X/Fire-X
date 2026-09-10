import json
import pandas as pd
import pytest
from app.ml.reference_bundle import load_reference_bundle,ReferenceBundleError
from app.ml.reference_audit import audit


def bundle(tmp_path,invalid_road=False):
    polygon={'type':'Polygon','coordinates':[[[77,21],[79,21],[79,23],[77,23],[77,21]]]}
    specs=[('administrative','administrative',polygon),('water','water',polygon),
        ('transport','road',polygon if invalid_road else {'type':'LineString','coordinates':[[78,21],[78,23]]})]
    layers=[]
    for role,category,geom in specs:
        file=tmp_path/f'{role}.geojson'
        file.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','id':role+'-unit',
            'properties':{'category':category,'name':'UNIT GEOMETRY','admin_level':4},'geometry':geom}],
            'coverage':{category:polygon}}))
        layers.append({'name':role,'role':role,'path':file.name,'source':'UNIT TEST ONLY','version':'test-v1','crs':'EPSG:4326'})
    path=tmp_path/'bundle.json';path.write_text(json.dumps({'version':1,'layers':layers}));return path


def test_admin_water_roads_and_measured_coverage(tmp_path):
    path=bundle(tmp_path)
    dataset,provenance=load_reference_bundle(path)
    assert dataset.available_categories=={'water','road','administrative'}
    assert len(provenance['layers'])==3
    events=tmp_path/'events.parquet'
    pd.DataFrame([{'event_id':'UNIT','centroid_latitude':22,'centroid_longitude':78}]).to_parquet(events)
    report=audit(events,path,tmp_path/'audit.json')
    assert report['events_with_administrative_match']==1
    assert report['events'][0]['covered_full_1km_buffer']['water']
    assert report['events'][0]['distances_km']['road']==0
    assert report['training_ready'] is False


def test_invalid_transport_geometry_rejected(tmp_path):
    with pytest.raises(ReferenceBundleError,match='geometry'):load_reference_bundle(bundle(tmp_path,invalid_road=True))
