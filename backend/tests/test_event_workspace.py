"""Isolated API integration for imported observations and annotation revisions."""
from pathlib import Path
from datetime import datetime,timezone
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base,get_db
from app.auth import create_access_token
from app.models import User,Hotspot
from app.event_models import ThermalEvent,EventPrediction,EventAnnotation
from app.models import SatelliteValidation
from app.ml.import_events import import_events

@pytest.fixture
def workspace(tmp_path):
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        users=[User(email=f'{i}@unit.invalid',name=f'Unit {i}',role=role,password_hash='disabled',is_active=True) for i,role in enumerate(['analyst','analyst','viewer'])]
        db.add_all(users);db.commit()
        headers=[{'Authorization':'Bearer '+create_access_token(u)} for u in users]
        from app.ml.data.preprocessing import preprocess
        from app.ml.build_dataset import build_files
        source=Path(__file__).resolve().parents[2]/'data'/'samples'/'firms_nasa_tutorial.csv'
        clean=tmp_path/'clean.parquet';path=tmp_path/'events.parquet'
        preprocess(source,clean,tmp_path/'raw',source='NASA published tutorial, test only')
        build_files(clean,path)
        result=import_events(path.resolve(),db);db.commit()
        assert result['event_count']==3
        assert import_events(path.resolve(),db)['imported_events']==0
        db.commit()
    def database():
        with Session(engine) as db: yield db
    previous=app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db]=database
    try: yield TestClient(app),headers,engine
    finally:
        if previous:app.dependency_overrides[get_db]=previous
        else:app.dependency_overrides.pop(get_db,None)
        engine.dispose()


def test_event_api_is_authenticated_and_evidence_is_honest(workspace):
    client,headers,_=workspace
    assert client.get('/api/v1/thermal-events').status_code==401
    status=client.get('/api/v1/thermal-events/status',headers=headers[0]).json()
    assert status['event_count']==3 and status['training_ready'] is False
    result=client.get('/api/v1/thermal-events?limit=1',headers=headers[0]).json()
    assert len(result['items'])==1 and result['total']==3
    event=result['items'][0]
    assert event['intelligence']['decision']=='Unknown' and event['intelligence']['confidence'] is None
    detail=client.get('/api/v1/thermal-events/'+event['event_id'],headers=headers[0]).json()
    assert detail['observations'] and detail['annotations']==[]
    assert client.get('/api/v1/thermal-events/missing',headers=headers[0]).status_code==404


def test_annotation_workflow_reviewer_and_revision_guards(workspace):
    client,headers,engine=workspace
    event=client.get('/api/v1/thermal-events',headers=headers[0]).json()['items'][0]
    url='/api/v1/thermal-events/'+event['event_id']+'/annotations'
    # Deliberately Unknown unit annotation; never a project training label.
    body={'expected_revision':0,'action':'submit','label':'Unknown','confidence':.9,'quality':'A','source':'UNIT TEST ONLY','evidence':['unit://fixture']}
    assert client.post(url,json=body,headers=headers[2]).status_code==403
    assert client.post(url,json=body,headers=headers[0]).status_code==200
    assert client.post(url,json=body,headers=headers[0]).status_code==409
    body.update(expected_revision=1,action='approve')
    assert client.post(url,json=body,headers=headers[0]).status_code==403
    result=client.post(url,json=body,headers=headers[1])
    assert result.status_code==200 and result.json()['training_eligible'] is False
    assert result.json()['annotation']['review_status']=='approved'
    records=client.get('/api/v1/thermal-events/annotations/export',headers=headers[0]).json()
    assert len(records)==1 and records[0]['reviewer']!=records[0]['annotator']
    with Session(engine) as db: assert len(db.scalars(select(EventAnnotation)).all())==2


def test_planet_catalog_has_no_invented_measurements(monkeypatch):
    from app.providers.satellite import LiveSatelliteProvider
    import httpx
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'features':[{'id':'unit-image','properties':{'acquired':'2025-01-01T00:00Z','cloud_cover':.1}}]}
    monkeypatch.setattr(httpx.Client,'post',lambda *a,**k:Response())
    hotspot=Hotspot(id=1,latitude=22,longitude=78,acquisition_time=datetime(2025,1,1,tzinfo=timezone.utc),frp=100,classification='Industrial Fire')
    result=LiveSatelliteProvider().validate(hotspot)
    assert result['status']=='NOT VALIDATED'
    for key in ('smoke_indication','burn_area_ha','fire_extent_km2','ndvi_before','ndvi_after'): assert result[key] is None
    assert 'Catalog metadata only' in result['notes']


def test_null_satellite_measurements_survive_database(workspace):
    _,_,engine=workspace
    with Session(engine) as db:
        row=SatelliteValidation(hotspot_id=1,status='NOT VALIDATED',provider='planet',smoke_indication=None,burn_area_ha=None,ndvi_before=None)
        db.add(row);db.commit();db.refresh(row)
        assert row.smoke_indication is None and row.burn_area_ha is None and row.ndvi_before is None


def test_event_date_filters_and_explanation_without_model(workspace):
    client,headers,_=workspace
    assert client.get('/api/v1/thermal-events?date_from=2025-01-01',headers=headers[0]).status_code==422
    event=client.get('/api/v1/thermal-events',headers=headers[0]).json()['items'][0]
    assert event['start_time'].endswith('+00:00')
    url='/api/v1/thermal-events/'+event['event_id']
    assert client.get(url+'/explanation',headers=headers[2]).status_code==403
    result=client.get(url+'/explanation?shap=true',headers=headers[0]).json()
    assert result['decision']=='Unknown' and result['explanation']['shap']['available'] is False
    assert client.post(url+'/analyze',headers=headers[0]).status_code==200


def test_unconfigured_providers_are_explicit_when_demo_disabled(monkeypatch):
    from app.config import settings
    from app.providers.satellite import get_satellite_provider
    from app.providers.firms import get_fire_provider,ProviderUnavailable
    monkeypatch.setattr(settings,'DEMO_MODE',False)
    monkeypatch.setattr(settings,'SATELLITE_API_KEY','')
    monkeypatch.setattr(settings,'FIRMS_API_KEY','')
    monkeypatch.setattr(settings,'FIRMS_MAP_KEY','')
    assert get_satellite_provider().mode=='unavailable'
    assert get_fire_provider().mode=='unavailable'
    with pytest.raises(ProviderUnavailable):get_fire_provider().fetch()


def test_live_ingest_never_uses_seeded_reference_context(monkeypatch):
    from app.config import settings
    from app.routers import ingest
    monkeypatch.setattr(settings,'DEMO_MODE',False)
    monkeypatch.setattr(settings,'REFERENCE_BUNDLE_PATH','')
    monkeypatch.setattr(ingest,'_dataset_cache',{})
    monkeypatch.setattr(ingest,'build_dataset',lambda:pytest.fail('Seeded GIS must not load for real ingestion'))
    dataset=ingest.get_dataset()
    assert not dataset.available_categories
    assert dataset.nearest_point('refinery',22,78) is None
