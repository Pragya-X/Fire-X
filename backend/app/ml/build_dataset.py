"""Build unlabeled thermal events: cluster, enrich, calculate history, save.

Edges require BOTH spatial and temporal proximity. Connected components may
chain beyond either threshold; candidate events are not verified incidents."""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd
import argparse
import json
from dataclasses import dataclass, asdict
from sklearn.neighbors import BallTree
from app.gis.engine import haversine_km, SpatialDataset
from pathlib import Path
from app.config import settings
from app.ml.spatial_features import event_spatial_features, load_reference_geojson
from app.ml.datasets import typed_events, validate_event_dataset, feature_schema, SCHEMA_VERSION, EVENT_COLUMNS
from app.services.temporal import historical_features, analyze_detections


EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class ClusteringConfig:
    spatial_km: float = 1.0
    temporal_hours: float = 24.0

    def __post_init__(self):
        object.__setattr__(self, "spatial_km", float(self.spatial_km))
        object.__setattr__(self, "temporal_hours", float(self.temporal_hours))
        if not np.isfinite(self.spatial_km) or not 0 < self.spatial_km <= 100:
            raise ValueError('spatial_km must be in (0,100]')
        if not np.isfinite(self.temporal_hours) or self.temporal_hours <= 0:
            raise ValueError('temporal_hours must be positive')


def spherical_centroid(latitudes, longitudes) -> tuple[float, float]:
    lat, lon = np.radians(latitudes), np.radians(longitudes)
    x, y, z = np.mean(np.cos(lat)*np.cos(lon)), np.mean(np.cos(lat)*np.sin(lon)), np.mean(np.sin(lat))
    return float(np.degrees(np.arctan2(z, np.hypot(x,y)))), float(np.degrees(np.arctan2(y,x)))


def cluster_events(detections: pd.DataFrame, config: ClusteringConfig | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    config = config or ClusteringConfig()
    df = detections.copy()
    required = {'latitude','longitude','acquisition_time','detection_id','frp','brightness','daynight'}
    if not required <= set(df):
        raise ValueError(f'Missing clean detection columns: {sorted(required-set(df))}')
    if df.detection_id.isna().any() or df.detection_id.duplicated().any():
        raise ValueError('Detection identities must be present and unique')
    coords = df[['latitude','longitude']].to_numpy(dtype=float)
    if not np.isfinite(coords).all() or (abs(coords[:,0])>90).any() or (abs(coords[:,1])>180).any():
        raise ValueError('Invalid geographic coordinates')
    df['acquisition_time'] = pd.to_datetime(df.acquisition_time, utc=True, errors='raise')
    if df.acquisition_time.isna().any():
        raise ValueError('Missing acquisition time')
    df = df.sort_values(['acquisition_time','detection_id']).reset_index(drop=True)
    if df.empty:
        df['event_id'] = pd.Series(dtype=str)
        return pd.DataFrame(columns=EVENT_COLUMNS), df
    coords = df[['latitude','longitude']].to_numpy(dtype=float)
    tree = BallTree(np.radians(coords), metric='haversine')
    times = df.acquisition_time.astype('int64').to_numpy()/1e9
    parent = list(range(len(df)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, point in enumerate(coords):
        neighbors = tree.query_radius(np.radians([point]), r=config.spatial_km/EARTH_RADIUS_KM)[0]
        for j in neighbors:
            if j > i and abs(times[j]-times[i]) <= config.temporal_hours*3600:
                parent[root(int(j))] = root(i)
    groups: dict[int,list[int]] = {}
    for i in range(len(df)):
        groups.setdefault(root(i),[]).append(i)
    events = []
    df['event_id'] = ''
    for members in groups.values():
        group = df.iloc[members]
        signature = f'event-v1|{config.spatial_km}|{config.temporal_hours}|' + '|'.join(sorted(group.detection_id))
        event_id = 'EV-' + hashlib.sha256(signature.encode()).hexdigest()[:20]
        df.loc[members,'event_id'] = event_id
        lat, lon = spherical_centroid(group.latitude.to_numpy(), group.longitude.to_numpy())
        row = dict(event_id=event_id, centroid_latitude=lat, centroid_longitude=lon,
            start_time=group.acquisition_time.min(), end_time=group.acquisition_time.max(),
            duration_minutes=(group.acquisition_time.max()-group.acquisition_time.min()).total_seconds()/60,
            detection_count=len(group),
            spatial_radius_km=max(haversine_km(lat,lon,r.latitude,r.longitude) for r in group.itertuples()),
            day_detection_ratio=float((group.daynight=='D').sum()/len(group)),
            night_detection_ratio=float((group.daynight=='N').sum()/len(group)),
            unknown_daynight_ratio=float(group.daynight.isna().sum()/len(group)))
        for field, stats in [('frp',('mean','max','min','std')),('brightness',('mean','max'))]:
            values = group[field].dropna()
            for stat in stats:
                row[f'{stat}_{field}'] = (float(values.std(ddof=0)) if stat=='std' else float(getattr(values,stat)())) if len(values) else None
        for field in ('satellite','instrument'):
            row[field] = '|'.join(sorted(set(group[field].dropna().astype(str)))) if field in group else None
        events.append(row)
    return pd.DataFrame(events,columns=EVENT_COLUMNS).sort_values(['start_time','event_id']).reset_index(drop=True), df


def build_event_dataset(clean: pd.DataFrame, *, references: SpatialDataset | None = None,
                        config: ClusteringConfig | None = None, history_radius_km: float = 1.0) -> tuple[pd.DataFrame,pd.DataFrame,dict]:
    if not np.isfinite(history_radius_km) or not 0 < history_radius_km <= 100:
        raise ValueError('history_radius_km must be in (0,100]')
    if 'data_source' not in clean or clean.data_source.isna().any():
        raise ValueError('Missing detection provenance: use preprocessing first')
    for field in ('frp','brightness'):
        if field not in clean: raise ValueError(f'Missing clean field {field}')
        valid=clean[field].dropna().to_numpy(dtype=float)
        if not np.isfinite(valid).all() or (valid<0).any() or (field=='brightness' and (valid==0).any()):
            raise ValueError(f'Invalid clean measurement {field}')
    events, membership = cluster_events(clean,config)
    tree = BallTree(np.radians(membership[['latitude','longitude']].to_numpy(float)),metric='haversine') if len(membership) else None
    rows=[]
    for event in events.to_dict('records'):
        lat,lon=event['centroid_latitude'],event['centroid_longitude']
        nearby=tree.query_radius(np.radians([[lat,lon]]),r=history_radius_km/EARTH_RADIUS_KM)[0]
        history=membership.iloc[nearby]
        history=history[(history.acquisition_time<event['start_time']) & (history.acquisition_time>=event['start_time']-pd.Timedelta(days=90))]
        stats=historical_features(history.to_dict('records'),reference_time=event['start_time'].to_pydatetime(),
            current_frp=event['mean_frp'],latitude=lat,longitude=lon,radius_km=history_radius_km)
        members=membership[membership.event_id==event['event_id']]
        temporal=analyze_detections(history.acquisition_time.tolist()+members.acquisition_time.tolist(),
            window_days=90,now=event['end_time'].to_pydatetime())
        spatial=event_spatial_features(references,lat,lon)
        # Evidence is observed context, not a verified industrial-source label.
        evidence = {'historical_active_days_90d':stats['active_days_90d'],
            'current_event_active_days':len(set(members.acquisition_time.dt.date)),'historical_std_frp':stats['historical_std_frp'],
            'spatial_location_variance_km2':stats['spatial_location_variance'],
            'industrial_distance_km':spatial['dist_nearest_industrial_km'],
            'score_policy':'observed-day cadence heuristic; not trained or scientifically calibrated'}
        rows.append({**event,**spatial,**stats,'persistence_score':temporal['persistence_score'],
            'temporal_pattern':temporal['pattern'],'persistence_evidence':json.dumps(evidence,sort_keys=True,allow_nan=False),
            'data_source':'|'.join(sorted(set(members.data_source.astype(str)))),
            'reference_source':references.provenance.get('source','explicit-in-memory-test') if references else None,
            'schema_version':SCHEMA_VERSION})
    output=typed_events(pd.DataFrame(rows))
    report=validate_event_dataset(output)
    if report['detection_count']!=len(clean): raise ValueError('Detection membership conservation failed')
    return output,membership,report


def build_files(input_path: Path, output: Path, *, reference_path: Path | None = None,
                reference_source: str | None = None, reference_crs: str = 'EPSG:4326',
                config: ClusteringConfig | None = None, history_radius_km: float = 1.0,
                reference_bundle: Path | None = None) -> dict:
    config=config or ClusteringConfig()
    if reference_path and not reference_source:
        raise ValueError('--reference-source required with reference geometry')
    if reference_path and reference_bundle:
        raise ValueError('Use either --references or --reference-bundle')
    provenance = {}
    if reference_bundle:
        from app.ml.reference_bundle import load_reference_bundle, ReferenceBundleError
        try:
            references, provenance = load_reference_bundle(reference_bundle)
        except ReferenceBundleError as exc:
            output.parent.mkdir(parents=True,exist_ok=True)
            output.with_suffix('.reference_validation.json').write_text(json.dumps(exc.report,indent=2))
            raise
    else:
        references=load_reference_geojson(reference_path,source=reference_source,crs=reference_crs) if reference_path else None
    clean=pd.read_parquet(input_path)
    events,members,report=build_event_dataset(clean,references=references,config=config,history_radius_km=history_radius_km)
    manifest={**report,'input_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),
        'reference_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest() if reference_path else None,
        'reference_source':reference_source,'reference_crs':reference_crs if reference_path else None,
        'clustering':asdict(config),'history_radius_km':history_radius_km,
        'temporal_policy':'[event_start - 90 days, event_start); all current-event observations excluded',
        'data_sources':sorted(set(clean.data_source.dropna().astype(str))),
        'algorithm':'space/time connected components (DBSCAN min_samples=1); transitive chaining allowed', **provenance}
    manifest['input_path'] = str(input_path.resolve())
    validation_path = input_path.with_suffix('.validation.json')
    if validation_path.exists():
        validation = json.loads(validation_path.read_text())
        if validation.get('clean_sha256') and validation['clean_sha256'] != manifest['input_sha256']:
            raise ValueError('Preprocessing validation hash does not match clean input')
        if validation.get('clean_output_written') is False:
            raise ValueError('Preprocessing failed; refuse stale clean input')
        manifest['preprocessing_metadata'] = validation
    output.parent.mkdir(parents=True,exist_ok=True)
    events.to_parquet(output,index=False)
    members[['detection_id','event_id','acquisition_time','latitude','longitude']].to_parquet(output.with_suffix('.membership.parquet'),index=False)
    manifest['event_dataset_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    manifest['membership_sha256'] = hashlib.sha256(output.with_suffix('.membership.parquet').read_bytes()).hexdigest()
    output.with_suffix('.reference_validation.json').write_text(json.dumps(provenance,indent=2))
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False))
    output.with_suffix('.schema.json').write_text(json.dumps(feature_schema(),indent=2))
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path(settings.DATA_DIR)/'processed/firms_clean.parquet')
    parser.add_argument('--output',type=Path,default=Path(settings.DATA_DIR)/'ml/thermal_events.parquet')
    parser.add_argument('--references',type=Path)
    parser.add_argument('--reference-bundle',type=Path)
    parser.add_argument('--reference-source')
    parser.add_argument('--reference-crs',default='EPSG:4326')
    parser.add_argument('--spatial-km',type=float,default=1)
    parser.add_argument('--temporal-hours',type=float,default=24)
    parser.add_argument('--history-radius-km',type=float,default=1)
    args=parser.parse_args()
    report=build_files(args.input,args.output,reference_path=args.references,reference_source=args.reference_source,
        reference_crs=args.reference_crs,reference_bundle=args.reference_bundle,config=ClusteringConfig(args.spatial_km,args.temporal_hours),history_radius_km=args.history_radius_km)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
