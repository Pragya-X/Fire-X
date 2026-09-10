"""Read-only coverage, history and inspection diagnostics. Never authorizes training."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree
from app.ml.datasets import validate_event_dataset
from app.ml.build_dataset import EARTH_RADIUS_KM
from app.ml.reference_bundle import sha256

INDUSTRIAL_CONTEXT = ['dist_nearest_industrial_km','dist_refinery_km','dist_factory_km',
    'dist_powerplant_km','dist_mine_km','industrial_count_500m','industrial_count_1km',
    'industrial_count_5km','inside_industrial_polygon','nearest_facility_id','nearest_facility_type']
LANDCOVER_CONTEXT = ['dist_forest_km','dist_agriculture_km','inside_forest','inside_agriculture',
    'inside_urban','forest_fraction_1km','agriculture_fraction_1km','industrial_fraction_1km']
TEMPORAL_CONTEXT = ['historical_mean_frp','historical_std_frp','historical_max_frp',
    'time_since_previous_detection','frp_z_score','historical_mean_brightness']


def feature_coverage(events: pd.DataFrame) -> dict:
    return {name:{'non_null':int(events[name].notna().sum()), 'null':int(events[name].isna().sum()),
        'null_percentage':float(events[name].isna().mean()*100) if len(events) else None}
        for name in events.columns}


def history_diagnostics(events: pd.DataFrame, clean: pd.DataFrame, radius_km: float) -> pd.DataFrame:
    """Explain data availability, not fire type. Distinguish zero variance from no history."""
    if not np.isfinite(radius_km) or radius_km <= 0:
        raise ValueError('history radius must be positive')
    clean = clean.sort_values('acquisition_time').reset_index(drop=True)
    stamps = pd.to_datetime(clean.acquisition_time,utc=True)
    tree = BallTree(np.radians(clean[['latitude','longitude']].to_numpy(float)),metric='haversine') if len(clean) else None
    rows = []
    for event in events.itertuples():
        start = pd.Timestamp(event.start_time)
        lower = start-pd.Timedelta(days=90)
        older_count = int(stamps.searchsorted(start))
        window_count = older_count-int(stamps.searchsorted(lower))
        nearby = tree.query_radius(np.radians([[event.centroid_latitude,event.centroid_longitude]]),r=radius_km/EARTH_RADIUS_KM)[0] if tree else []
        local = clean.iloc[nearby]
        local_times = pd.to_datetime(local.acquisition_time,utc=True)
        local = local[(local_times>=lower)&(local_times<start)]
        frp = local.frp.dropna()
        unique_times = int(local.acquisition_time.nunique())
        if older_count == 0: reason = 'NO_PRIOR_OBSERVATIONS'
        elif window_count == 0: reason = 'NO_PRIOR_IN_HISTORY_WINDOW'
        elif len(local) == 0: reason = 'NO_MATCH_WITHIN_HISTORY_RADIUS'
        elif len(frp) == 0: reason = 'MISSING_HISTORICAL_FRP'
        elif len(frp) < 2 or unique_times < 2: reason = 'INSUFFICIENT_HISTORY'
        elif float(frp.std(ddof=0)) == 0: reason = 'ZERO_HISTORICAL_VARIANCE'
        elif pd.isna(event.mean_frp): reason = 'CURRENT_FRP_MISSING'
        else: reason = 'AVAILABLE'
        rows.append({'event_id':event.event_id,'history_reason':reason,
            'prior_observations_all_locations':older_count,'prior_observations_90d_all_locations':window_count,
            'historical_detections':len(local),'historical_frp_count':len(frp),
            'historical_unique_times':unique_times,'baseline_available':bool(len(frp)),
            'history_detection_ids':local.detection_id.astype(str).tolist(),
            'window_start':lower.isoformat(),'window_end_exclusive':start.isoformat()})
    return pd.DataFrame(rows,columns=['event_id','history_reason','prior_observations_all_locations',
        'prior_observations_90d_all_locations','historical_detections','historical_frp_count',
        'historical_unique_times','baseline_available','history_detection_ids','window_start','window_end_exclusive'])


def clustering_audit(events: pd.DataFrame, config: dict) -> dict:
    spatial, hours = float(config['spatial_km']), float(config['temporal_hours'])
    flags = []
    for event in events.itertuples():
        reasons = []
        if event.spatial_radius_km > spatial: reasons.append('SPATIAL_CHAIN_REVIEW')
        if event.duration_minutes > hours*60: reasons.append('TEMPORAL_CHAIN_REVIEW')
        if reasons:
            flags.append({'event_id':event.event_id,'reasons':reasons,
                          'radius_km':float(event.spatial_radius_km),'duration_hours':float(event.duration_minutes/60)})
    pairs = []
    truncated = False
    if len(events):
        points = np.radians(events[['centroid_latitude','centroid_longitude']].to_numpy(float))
        tree = BallTree(points,metric='haversine')
        for i,point in enumerate(points):
            neighbors = tree.query_radius([point],r=spatial/EARTH_RADIUS_KM)[0]
            for j in neighbors:
                if j<=i: continue
                a,b = events.iloc[i],events.iloc[int(j)]
                gap = max(0,(max(a.start_time,b.start_time)-min(a.end_time,b.end_time)).total_seconds()/3600)
                if gap<=hours:
                    if len(pairs)>=1000:
                        truncated=True
                        break
                    pairs.append({'event_a':a.event_id,'event_b':b.event_id,'gap_hours':gap,
                                  'reason':'NEARBY_SEPARATE_CENTROIDS_REVIEW'})
            if truncated: break
    return {'parameters':config,'event_flags':flags,'nearby_separate_event_pairs':pairs,
        'pair_report_truncated_at_1000':truncated,'confirmed_over_merging':None,'confirmed_over_splitting':None,
        'maximum_radius_km':float(events.spatial_radius_km.max()) if len(events) else None,
        'maximum_duration_hours':float(events.duration_minutes.max()/60) if len(events) else None,
        'interpretation':'Flags identify review candidates, not proven errors. Chaining is allowed by connectivity. Centroid proximity does not prove member connectivity.',
        'parameter_change_recommendation':None,'human_inspection_completed':False}


def inspection_sample(events: pd.DataFrame, membership: pd.DataFrame, clean: pd.DataFrame,
                      history: pd.DataFrame, size: int) -> pd.DataFrame:
    if size<1: raise ValueError('inspection size must be positive')
    selected = []
    # Deterministic coverage of missing/present context plus large radius/duration.
    for field in ('dist_nearest_industrial_km','historical_mean_frp'):
        for present in (True,False):
            candidates=events[events[field].notna()==present].sort_values('event_id')
            if len(candidates): selected.append(candidates.iloc[0].event_id)
    for field in ('spatial_radius_km','duration_minutes','detection_count'):
        if len(events): selected.append(events.sort_values([field,'event_id'],ascending=[False,True]).iloc[0].event_id)
    selected=list(dict.fromkeys(selected+sorted(events.event_id.tolist())))[:size]
    sample = events.set_index('event_id').reindex(selected).reset_index()
    details = clean.merge(membership[['detection_id','event_id']],on='detection_id',validate='one_to_one')
    groups = {event_id:group for event_id,group in details.groupby('event_id')}
    member_fields=[c for c in ('detection_id','latitude','longitude','acquisition_time','frp','brightness','satellite','instrument','daynight') if c in details]
    sample['member_detections']=[groups[event_id][member_fields].to_json(orient='records',date_format='iso') for event_id in selected]
    sample=sample.merge(history,on='event_id',how='left',validate='one_to_one')
    sample['history_detection_ids']=sample.history_detection_ids.map(json.dumps)
    sample['human_review_status']='PENDING'
    return sample.rename(columns={'centroid_latitude':'latitude','centroid_longitude':'longitude'})


def _markdown_table(frame: pd.DataFrame) -> str:
    def cell(value):
        return ('unavailable' if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)) else str(value)).replace('|','\\|').replace('\n',' ')
    rows=['| '+' | '.join(map(cell,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']
    rows += ['| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None)]
    return '\n'.join(rows)


def _write_report(report: dict, prefix: Path) -> None:
    prefix.parent.mkdir(parents=True,exist_ok=True)
    prefix.with_suffix('.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    lines=['# Dataset readiness: TRAINING BLOCKED', '',
        f"Dataset requested: `{report['event_dataset']}`",'',
        f"Status: {report['status']}. Events: {report.get('event_count')}; detections: {report.get('detection_count')}.", '',
        '## Readiness', '',_markdown_table(pd.DataFrame([
            {'state':key,'ready':value['ready'],'reason':'; '.join(value['reasons'])}
            for key,value in report['readiness'].items()])), '', '## Blockers','']
    lines += [f'- {reason}' for reason in report['blockers']]
    lines += ['', '## Required human work','',
        '- Supply sourced India FIRMS CSV/Parquet observations, industrial references, and land-cover polygons with coverage metadata.',
        '- Inspect the generated sample and all flagged clusters; verify facility identity, geometry, coverage and historical availability.',
        '- Review representativeness and source coverage before starting a separate labeling phase. No labels or model results are generated here.']
    if 'feature_coverage' in report:
        lines += ['', '## Observed feature coverage (no target percentages)','',
            _markdown_table(pd.DataFrame([{'feature':key,**value} for key,value in report['feature_coverage'].items()])),
            '', '## Historical diagnostics','', json.dumps(report['history_reason_counts'],indent=2),
            '', '## Clustering audit','', '```json',json.dumps(report['clustering_audit'],indent=2),'```',
            '', '## Exact events for review','']
        lines += [f'- `{event_id}`' for event_id in report['inspection_event_ids']]
    prefix.with_suffix('.md').write_text('\n'.join(lines)+'\n')


def generate_report(events_path: Path, clean_path: Path, prefix: Path,
                    inspection_prefix: Path, *, sample_size: int = 20) -> dict:
    """Always emit blockers for missing/invalid inputs; never changes model/readiness artifacts."""
    if sample_size<1: raise ValueError('sample size must be positive')
    manifest_path=events_path.with_suffix('.manifest.json')
    membership_path=events_path.with_suffix('.membership.parquet')
    missing=[str(path) for path in (events_path,clean_path,manifest_path,membership_path) if not path.exists()]
    report={'event_dataset':str(events_path),'clean_input':str(clean_path),
        'status':'MISSING_INPUTS' if missing else 'PENDING_VALIDATION', 'event_count':None,'detection_count':None,
        'training_ready':False,'missing_files':missing,
        'label_counts':{'industrial_fire':0,'persistent_industrial_source':0,'wildfire':0,'other':0,'uncertain':0},
        'label_quality_counts':{'A':0,'B':0,'C':0},'label_policy':'No label input assessed in this data-readiness stage; zero counts describe supplied labels, not event classes.',
        'readiness':{
            'DATA_PIPELINE_READY':{'ready':False,'reasons':['MISSING_OR_INVALID_ARTIFACTS']},
            'REFERENCE_COVERAGE_READY':{'ready':False,'reasons':['REFERENCE_COVERAGE_NOT_REVIEWED']},
            'TEMPORAL_HISTORY_READY':{'ready':False,'reasons':['TEMPORAL_COVERAGE_NOT_REVIEWED']},
            'LABELS_READY':{'ready':False,'reasons':['NO_REVIEWED_LABELS_SUPPLIED']},
            'TRAINING_READY':{'ready':False,'reasons':['TRAINING_PROHIBITED_IN_THIS_STAGE','NO_REVIEWED_LABELS_SUPPLIED']}},
        'blockers':['NO_REVIEWED_LABELS_SUPPLIED','REPRESENTATIVE_INDIA_DATA_REVIEW_REQUIRED'],
        'event_dataset_validated':False}
    if missing:
        report['blockers'].append('MISSING_INPUT_FILES')
        _write_report(report,prefix)
        return report
    try:
        manifest=json.loads(manifest_path.read_text())
        events=pd.read_parquet(events_path)
        clean=pd.read_parquet(clean_path)
        members=pd.read_parquet(membership_path)
        validate_event_dataset(events)
        if manifest.get('training_ready') is not False:
            raise ValueError('Expected existing training_ready=false; no gate changes allowed')
        if sha256(clean_path)!=manifest.get('input_sha256'):
            raise ValueError('Clean input hash mismatch')
        for key,path in (('event_dataset_sha256',events_path),('membership_sha256',membership_path)):
            if manifest.get(key) and sha256(path)!=manifest[key]:
                raise ValueError(f'{key} mismatch')
        if len(members)!=len(clean) or members.detection_id.duplicated().any() or clean.detection_id.duplicated().any():
            raise ValueError('Invalid detection membership cardinality')
        if set(members.detection_id)!=set(clean.detection_id) or set(members.event_id)!=set(events.event_id):
            raise ValueError('Membership identities do not match observations/events')
        counts=members.groupby('event_id').size()
        if any(int(counts[event.event_id])!=event.detection_count for event in events.itertuples()):
            raise ValueError('Event detection count differs from membership')
        if manifest.get('reference_bundle_path'):
            from app.ml.reference_bundle import load_reference_bundle
            _,provenance=load_reference_bundle(Path(manifest['reference_bundle_path']))
            if provenance['reference_sha256']!=manifest['reference_sha256']:
                raise ValueError('Reference bundle/input hash mismatch')
        history=history_diagnostics(events,clean,float(manifest['history_radius_km']))
        for event in events.itertuples():
            diagnostic=history[history.event_id==event.event_id].iloc[0]
            if int(event.detections_90d)!=diagnostic.historical_detections:
                raise ValueError('Historical detection count inconsistent with source observations')
        sample=inspection_sample(events,members,clean,history,sample_size)
        coverage=feature_coverage(events)
        report.update(status='VALIDATED_UNREVIEWED',event_dataset_validated=True,event_count=len(events),detection_count=len(members),
            schema_version=manifest['schema_version'],training_ready_before=manifest['training_ready'],
            date_coverage=None if events.empty else {'start':events.start_time.min().isoformat(),'end':events.end_time.max().isoformat()},
            geographic_coverage=None if events.empty else {'west':float(events.centroid_longitude.min()),'south':float(events.centroid_latitude.min()),'east':float(events.centroid_longitude.max()),'north':float(events.centroid_latitude.max())},
            feature_coverage=coverage,
            industrial_context_coverage={key:coverage[key] for key in INDUSTRIAL_CONTEXT},
            landcover_context_coverage={key:coverage[key] for key in LANDCOVER_CONTEXT},
            temporal_context_coverage={key:coverage[key] for key in TEMPORAL_CONTEXT},
            history_reason_counts=dict(Counter(history.history_reason)),
            history_diagnostics=json.loads(history.to_json(orient='records')),
            clustering_audit=clustering_audit(events,manifest['clustering']),
            inspection_event_ids=sample.event_id.tolist(),
            reference_provenance={key:manifest.get(key) for key in ('reference_source','reference_sha256','reference_crs','industrial_reference_source','industrial_reference_version','landcover_source','landcover_version','layers')},
            source_event_sha256=sha256(events_path),source_clean_sha256=sha256(clean_path),
            observation_coverage_note='Counts describe supplied detections, not continuous sensor observation. Source/archive coverage needs human review.',
            inspection_csv=str(inspection_prefix.with_suffix('.csv')))
        report['readiness']['DATA_PIPELINE_READY']={'ready':bool(len(events)), 'reasons':[] if len(events) else ['EMPTY_EVENT_DATASET']}
        reference_reasons=['REFERENCE_COVERAGE_NOT_REVIEWED']
        if not manifest.get('reference_sha256'): reference_reasons.append('NO_REFERENCE_BUNDLE')
        if not events[INDUSTRIAL_CONTEXT].notna().any().any(): reference_reasons.append('NO_INDUSTRIAL_CONTEXT')
        if not events[LANDCOVER_CONTEXT].notna().any().any(): reference_reasons.append('NO_LANDCOVER_CONTEXT')
        if not manifest.get('industrial_reference_source'): reference_reasons.append('INDUSTRIAL_SOURCE_NOT_SEPARATELY_DOCUMENTED')
        if not manifest.get('landcover_source'): reference_reasons.append('LANDCOVER_SOURCE_NOT_SEPARATELY_DOCUMENTED')
        report['readiness']['REFERENCE_COVERAGE_READY']['reasons']=reference_reasons
        temporal_reasons=['TEMPORAL_COVERAGE_NOT_REVIEWED']
        if not events.historical_mean_frp.notna().any(): temporal_reasons.append('NO_HISTORICAL_FRP_BASELINES')
        report['readiness']['TEMPORAL_HISTORY_READY']['reasons']=temporal_reasons
        report['blockers'] += reference_reasons+temporal_reasons
        if len(events) and not (events.centroid_longitude.between(67,98)&events.centroid_latitude.between(6,38)).all():
            report['blockers'].append('EVENTS_OUTSIDE_INDIA_AUDIT_ENVELOPE')
        report['blockers'] = list(dict.fromkeys(report['blockers']))
        inspection_prefix.parent.mkdir(parents=True,exist_ok=True)
        sample.to_csv(inspection_prefix.with_suffix('.csv'),index=False)
        summary_columns=['event_id','latitude','longitude','start_time','end_time','detection_count','mean_frp','max_frp','spatial_radius_km','nearest_facility_id','nearest_facility_type','dist_nearest_industrial_km','inside_forest','inside_agriculture','inside_urban','historical_detections','history_reason','persistence_score']
        # Object conversion allows nullable extension dtypes to display missing text.
        summary=sample[summary_columns].astype(object)
        lines=['# Event inspection — human review pending','',f'Source: `{events_path}`. Not ground-truth annotations.', '',_markdown_table(summary),'',
            'Full member detections and historical IDs are in the CSV. Review candidates:', '']
        for row in sample.to_dict('records'):
            lines += [f"## {row['event_id']}",'','Member detections:','```json',row['member_detections'],'```',
                      'Historical detection IDs:','```json',row['history_detection_ids'],'```','']
        inspection_prefix.with_suffix('.md').write_text('\n'.join(lines))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        report['status']='INVALID_INPUTS'
        report['event_dataset_validated']=False
        report['readiness']['DATA_PIPELINE_READY']={'ready':False,'reasons':['ARTIFACT_VALIDATION_FAILED']}
        report['blockers'].append(f'ARTIFACT_VALIDATION_FAILED: {exc}')
    _write_report(report,prefix)
    return report


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events',type=Path,default=Path('data/ml/thermal_events_india.parquet'))
    parser.add_argument('--clean',type=Path,default=Path('data/processed/firms_india_clean.parquet'))
    parser.add_argument('--report-prefix',type=Path,default=Path('reports/ml/india_dataset_validation'))
    parser.add_argument('--inspection-prefix',type=Path,default=Path('reports/ml/event_inspection_sample'))
    parser.add_argument('--sample-size',type=int,default=20)
    args=parser.parse_args()
    report=generate_report(args.events,args.clean,args.report_prefix,args.inspection_prefix,sample_size=args.sample_size)
    print(json.dumps({'status':report['status'],'training_ready':False,'readiness':report['readiness'],'blockers':report['blockers']},indent=2))
    # Exit 2 intentionally signals the training block, including valid but unlabeled datasets.
    raise SystemExit(2)


if __name__=='__main__':
    main()
