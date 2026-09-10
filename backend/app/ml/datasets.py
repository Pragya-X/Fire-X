"""Versioned nullable event schema, separate from the legacy demo model vector."""
from __future__ import annotations
import numpy as np
import pandas as pd
from app.ml.spatial_features import SPATIAL_FIELDS

EVENT_COLUMNS = ['event_id','centroid_latitude','centroid_longitude','start_time','end_time',
    'duration_minutes','detection_count','mean_frp','max_frp','min_frp','std_frp',
    'mean_brightness','max_brightness','spatial_radius_km','day_detection_ratio',
    'night_detection_ratio','unknown_daynight_ratio','satellite','instrument']

SCHEMA_VERSION = 'thermal-events-v1'
TEMPORAL_FIELDS = [f'detections_{w}' for w in ('24h','7d','30d','90d')] + [f'active_days_{w}' for w in ('7d','30d','90d')] + [
    'time_since_previous_detection','historical_mean_frp','historical_median_frp','historical_std_frp','historical_max_frp',
    'frp_delta_from_baseline','frp_ratio_to_baseline','frp_z_score','historical_mean_brightness',
    'mean_detection_interval_hours','std_detection_interval_hours','same_location_recurrence',
    'spatial_location_variance','day_ratio','night_ratio','history_start','history_end_exclusive']
EXTRA_FIELDS = ['persistence_score','temporal_pattern','persistence_evidence','data_source','reference_source','schema_version']
COLUMNS = EVENT_COLUMNS + SPATIAL_FIELDS + TEMPORAL_FIELDS + EXTRA_FIELDS
STRING_FIELDS = {'event_id','satellite','instrument','nearest_facility_id','nearest_facility_type','history_start','history_end_exclusive',
    'temporal_pattern','persistence_evidence','data_source','reference_source','schema_version'}
BOOL_FIELDS = {'inside_industrial_polygon','inside_forest','inside_agriculture','inside_urban'}
TIME_FIELDS = {'start_time','end_time'}
INTEGER_FIELDS = {'detection_count','industrial_count_500m','industrial_count_1km','industrial_count_5km'} | {c for c in TEMPORAL_FIELDS if c.startswith(('detections_','active_days_'))}


def typed_events(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.reindex(columns=COLUMNS).copy()
    for col in COLUMNS:
        if col in TIME_FIELDS:
            frame[col] = pd.to_datetime(frame[col],utc=True)
        else:
            dtype = 'string' if col in STRING_FIELDS else 'boolean' if col in BOOL_FIELDS else 'Int64' if col in INTEGER_FIELDS else 'Float64'
            frame[col] = frame[col].astype(dtype)
    return frame


def validate_event_dataset(frame: pd.DataFrame) -> dict:
    missing = sorted(set(COLUMNS)-set(frame))
    if missing:
        raise ValueError(f'Missing event columns: {missing}')
    if frame.event_id.isna().any() or frame.event_id.duplicated().any():
        raise ValueError('Event identifiers must be unique and non-null')
    if frame.start_time.isna().any() or frame.end_time.isna().any() or (frame.end_time<frame.start_time).any():
        raise ValueError('Invalid event time range')
    if frame.centroid_latitude.isna().any() or not frame.centroid_latitude.between(-90,90).all() or frame.centroid_longitude.isna().any() or not frame.centroid_longitude.between(-180,180).all():
        raise ValueError('Invalid event coordinates')
    if (frame.detection_count<1).any() or frame.detection_count.isna().any():
        raise ValueError('Events require at least one detection')
    for col in COLUMNS:
        if col in STRING_FIELDS | BOOL_FIELDS | TIME_FIELDS: continue
        values = frame[col].dropna().to_numpy(dtype=float)
        if not np.isfinite(values).all(): raise ValueError(f'Nonfinite feature {col}')
        if (col.endswith('_ratio') or '_fraction_' in col or col=='same_location_recurrence') and col!='frp_ratio_to_baseline':
            if ((values<0)|(values>1)).any(): raise ValueError(f'Invalid proportion {col}')
    return {'schema_version':SCHEMA_VERSION,'event_count':len(frame),
        'detection_count':int(frame.detection_count.sum()),
        'null_counts':{c:int(frame[c].isna().sum()) for c in COLUMNS},
        'labels_required':False,'training_ready':False,
        'limitation':'Unlabeled event features only. Real reference coverage and reviewed labels must be assessed before training.'}


def feature_schema() -> dict:
    return {'version':SCHEMA_VERSION,'columns':[
        {'name':c,'dtype':'timestamp[UTC]' if c in TIME_FIELDS else 'string' if c in STRING_FIELDS else 'boolean' if c in BOOL_FIELDS else 'integer' if c in INTEGER_FIELDS else 'float',
         'nullable':c not in {'event_id','start_time','end_time','centroid_latitude','centroid_longitude','detection_count'}} for c in COLUMNS],
        'units':{'distance':'km','frp':'MW','brightness':'K','time_since_previous_detection':'hours','spatial_location_variance':'km^2','persistence_score':'heuristic 0–100'},
        'not_model_input':'Identifiers, provenance, times and evidence are audit context; future training must explicitly select leakage-safe features.'}
