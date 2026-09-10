"""Administrative assignment and measured reference coverage, without class labels."""
import argparse
import json
from pathlib import Path
import pandas as pd
from shapely.geometry import Point
from shapely.ops import transform
from app.gis.engine import local_transformer
from app.ml.reference_bundle import load_reference_bundle,sha256
from app.ml.training import write_json


def audit(events_path: Path,bundle_path: Path,output: Path) -> dict:
    dataset,provenance=load_reference_bundle(bundle_path)
    events=pd.read_parquet(events_path)
    rows=[]
    for event in events.itertuples():
        point=Point(event.centroid_longitude,event.centroid_latitude)
        buffer=Point(0,0).buffer(1000)
        project=local_transformer(event.centroid_latitude,event.centroid_longitude).transform
        administrative=[f for f in dataset.geometries('administrative') if f.geom.covers(point)]
        row={'event_id':event.event_id,'administrative_matches':[{'id':f.id,'name':f.name,
             'admin_level':f.meta.get('admin_level'),'source':f.meta.get('source')} for f in administrative],
             'covered_at_centroid':{},'covered_full_1km_buffer':{},'distances_km':{}}
        for cat in sorted(dataset.available_categories):
            coverage=dataset.coverage.get(cat)
            row['covered_at_centroid'][cat]=bool(coverage.covers(point)) if coverage is not None else None
            row['covered_full_1km_buffer'][cat]=bool(transform(project,coverage).covers(buffer)) if coverage is not None else None
        for cat in ('road','railway','pipeline','water'):
            nearest=dataset.nearest_geometry(cat,event.centroid_latitude,event.centroid_longitude)
            row['distances_km'][cat]=nearest['distance_km'] if nearest else None
        rows.append(row)
    report={'event_dataset_sha256':sha256(events_path),'reference_provenance':provenance,'event_count':len(rows),
        'events_with_administrative_match':sum(bool(r['administrative_matches']) for r in rows),
        'coverage_counts':{cat:sum(r['covered_at_centroid'].get(cat) is True for r in rows) for cat in dataset.available_categories},
        'events':rows,'training_ready':False,
        'limitations':['Administrative matches reflect the supplied boundary source, not a territorial adjudication.',
            'Null coverage means completeness was not declared. Point presence alone does not prove complete coverage.',
            'Road/water distances and administrative assignments are audit sidecars; the existing event schema remains unchanged.']}
    write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('events','bundle','output'): parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();report=audit(args.events,args.bundle,args.output)
    print(json.dumps({'event_count':report['event_count'],'training_ready':False}))

if __name__=='__main__':main()
