"""Atomic local CLI import of validated artifacts. Does not seed or label events."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from sqlalchemy import select
from app.database import SessionLocal, init_db
from app.event_models import ThermalEvent, EventPrediction, ThermalObservation, ReferenceFacility
from app.ml.datasets import validate_event_dataset
from app.ml.reference_bundle import sha256, load_reference_bundle
from app.services.event_intelligence import predict_event


def import_events(path: Path, db) -> dict:
    manifest=json.loads(path.with_suffix('.manifest.json').read_text())
    clean_path=Path(manifest['input_path'])
    membership_path=path.with_suffix('.membership.parquet')
    for candidate,key in ((path,'event_dataset_sha256'),(clean_path,'input_sha256'),(membership_path,'membership_sha256')):
        if sha256(candidate)!=manifest.get(key): raise ValueError(f'Artifact hash mismatch: {key}')
    frame=pd.read_parquet(path)
    validate_event_dataset(frame)
    members=pd.read_parquet(membership_path)
    clean=pd.read_parquet(clean_path)
    if members.detection_id.duplicated().any() or set(members.event_id)!=set(frame.event_id) or set(members.detection_id)!=set(clean.detection_id):
        raise ValueError('Invalid event membership')
    counts=members.groupby('event_id').size()
    if any(counts[row.event_id]!=row.detection_count for row in frame.itertuples()): raise ValueError('Event detection counts mismatch')
    observations=clean.merge(members[['event_id','detection_id']],on='detection_id',validate='one_to_one')
    digest=sha256(path)
    bundle=None
    if manifest.get('reference_bundle_path'):
        bundle,provenance=load_reference_bundle(Path(manifest['reference_bundle_path']))
        if provenance['reference_sha256']!=manifest['reference_sha256']: raise ValueError('Stale reference bundle')
    added=0
    # Caller owns transaction; any inconsistency rolls back all changes.
    for row in json.loads(frame.to_json(orient='records',date_format='iso')):
        existing=db.get(ThermalEvent,row['event_id'])
        if existing:
            if existing.dataset_sha256!=digest: raise ValueError('Event already imported from a different artifact; explicit version migration required')
            continue
        event=ThermalEvent(event_id=row['event_id'],latitude=row['centroid_latitude'],longitude=row['centroid_longitude'],
            start_time=pd.Timestamp(row['start_time']).to_pydatetime(),end_time=pd.Timestamp(row['end_time']).to_pydatetime(),
            facility_id=row.get('nearest_facility_id'),features=row,dataset_sha256=digest,
            provenance={'data_source':row.get('data_source'),'dataset_sha256':digest,'input_sha256':manifest['input_sha256'],
                'reference_sha256':manifest.get('reference_sha256'),'data_type':'observations','training_ready':False})
        db.add(event); db.flush()
        intelligence=predict_event(row)
        db.add(EventPrediction(event_id=event.event_id,model_version=intelligence['model_version'],
            decision=intelligence['decision'],confidence=intelligence['confidence'],intelligence=intelligence))
        added+=1
    for row in json.loads(observations.to_json(orient='records',date_format='iso')):
        old=db.get(ThermalObservation,row['detection_id'])
        if old:
            if old.event_id!=row['event_id']: raise ValueError('Detection cannot be assigned to multiple events')
            continue
        db.add(ThermalObservation(detection_id=row['detection_id'],event_id=row['event_id'],latitude=row['latitude'],longitude=row['longitude'],
            acquisition_time=pd.Timestamp(row['acquisition_time']).to_pydatetime(),measurements=row))
    if bundle:
        from shapely.geometry import Point
        from app.ml.spatial_features import INDUSTRIAL
        for cat in INDUSTRIAL:
            for facility in bundle.points(cat):
                footprint=next((f.geom for f in bundle.geometries('industrial') if f.id==facility.id),Point(facility.lon,facility.lat))
                old=db.get(ReferenceFacility,facility.id)
                if old:
                    if old.provenance.get('reference_sha256')!=manifest['reference_sha256']:
                        raise ValueError('Facility already has different provenance; explicit version migration required')
                    continue
                db.add(ReferenceFacility(facility_id=facility.id,name=facility.name,facility_type=cat,
                    latitude=facility.lat,longitude=facility.lon,geometry_wkt=footprint.wkt,
                    provenance={**facility.meta,'reference_sha256':manifest['reference_sha256']}))
                db.flush()
    db.flush()
    return {'imported_events':added,'event_count':len(frame),'dataset_sha256':digest,'training_ready':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--events',type=Path,required=True)
    args=parser.parse_args();init_db()
    with SessionLocal.begin() as db: result=import_events(args.events,db)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
