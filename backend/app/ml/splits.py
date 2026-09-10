"""Purged, disjoint event splits; same facility or nearby locations form one group.

A spatial connected component can be larger than the radius through chains.
Temporal mode additionally removes all groups crossing time boundaries and
purges the feature history window. Empty/class-incomplete splits fail closed.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

@dataclass(frozen=True)
class SplitConfig:
    strategy: str = 'geographic'
    radius_km: float = 5.0
    history_days: int = 90
    train_fraction: float = .6
    validation_fraction: float = .2
    seed: int = 42
    train_end: str | None = None
    validation_end: str | None = None

    def __post_init__(self):
        if self.strategy not in ('group','geographic','temporal','facility'):
            raise ValueError('Unknown split strategy')
        if not np.isfinite(self.radius_km) or self.radius_km < 2 or self.history_days < 90:
            raise ValueError('Splits require >=2 km grouping and >=90 day history purge')
        if not 0 < self.train_fraction < 1 or not 0 < self.validation_fraction < 1-self.train_fraction:
            raise ValueError('Invalid split fractions')


def leakage_groups(frame: pd.DataFrame, radius_km: float) -> list[str]:
    if frame.event_id.isna().any() or frame.event_id.duplicated().any():
        raise ValueError('Duplicate or missing event IDs')
    coords = frame[['centroid_latitude','centroid_longitude']].to_numpy(dtype=float)
    if not np.isfinite(coords).all() or (np.abs(coords[:,0])>90).any() or (np.abs(coords[:,1])>180).any():
        raise ValueError('Invalid coordinates')
    parent = list(range(len(frame)))
    def find(i):
        while i != parent[i]:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(a,b):
        parent[find(b)] = find(a)
    if len(frame):
        # Bounding circles include each event's full member extent, preventing
        # two long/chained events from appearing spatially disjoint by centroid.
        extents=frame['spatial_radius_km'].fillna(0).to_numpy(dtype=float) if 'spatial_radius_km' in frame else np.zeros(len(frame))
        if not np.isfinite(extents).all() or (extents<0).any(): raise ValueError('Invalid event spatial extent')
        radii=extents+radius_km/2
        tree=BallTree(np.radians(coords),metric='haversine')
        neighbors,distances=tree.query_radius(np.radians(coords),r=(radii+radii.max())/6371.0088,return_distance=True)
        for i,(near,distance) in enumerate(zip(neighbors,distances)):
            for j,d in zip(near,distance):
                if d*6371.0088 <= radii[i]+radii[int(j)]+1e-9:
                    union(i,int(j))
    facilities = {}
    for i, fid in enumerate(frame.nearest_facility_id):
        if pd.notna(fid) and str(fid).strip():
            if fid in facilities: union(i, facilities[fid])
            facilities[fid] = i
    components = {}
    for i, eid in enumerate(frame.event_id): components.setdefault(find(i),[]).append(str(eid))
    names = {root: hashlib.sha256('|'.join(sorted(ids)).encode()).hexdigest()[:20] for root,ids in components.items()}
    return [names[find(i)] for i in range(len(frame))]


def make_splits(frame: pd.DataFrame, config: SplitConfig) -> tuple[pd.DataFrame, dict]:
    result = frame[['event_id']].copy()
    result['group_id'] = leakage_groups(frame, config.radius_km)
    result['split'] = 'excluded'
    if config.strategy == 'facility' and (frame.nearest_facility_id.isna() | frame.nearest_facility_id.astype('string').str.strip().eq('')).any():
        raise ValueError('Facility split requires verified facility identity for every event')
    if config.strategy == 'temporal':
        if not config.train_end or not config.validation_end:
            raise ValueError('Temporal split requires explicit train_end and validation_end')
        first, second = pd.Timestamp(config.train_end), pd.Timestamp(config.validation_end)
        if first.tzinfo is None or second.tzinfo is None or first >= second:
            raise ValueError('Cutoffs must be ordered timezone-aware timestamps')
        start, end = pd.to_datetime(frame.start_time, utc=True), pd.to_datetime(frame.end_time, utc=True)
        purge = pd.Timedelta(days=config.history_days)
        result.loc[end < first, 'split'] = 'train'
        result.loc[(start >= first+purge) & (end < second),'split'] = 'validation'
        result.loc[start >= second+purge,'split'] = 'test'
        # Includes excluded rows: groups touching a boundary/embargo are dropped.
        mixed = result.groupby('group_id')['split'].nunique()
        result.loc[result.group_id.isin(mixed[mixed>1].index),'split'] = 'excluded'
    else:
        groups = sorted(result.group_id.unique())
        if len(groups) < 3: raise ValueError('At least three independent location/facility groups required')
        rng = np.random.default_rng(config.seed)
        rng.shuffle(groups)
        a = min(len(groups)-2, max(1,int(len(groups)*config.train_fraction)))
        b = min(len(groups)-1, max(a+1,int(len(groups)*(config.train_fraction+config.validation_fraction))))
        mapping = {g:'train' if i<a else 'validation' if i<b else 'test' for i,g in enumerate(groups)}
        result['split'] = result.group_id.map(mapping)
    audit = audit_splits(frame, result)
    audit['config'] = asdict(config)
    audit['evaluation_scope'] = ('New locations/facilities, future windows with 90-day purge' if config.strategy=='temporal'
        else 'Unseen location/facility groups; overlapping calendar periods allowed; not a future-time benchmark')
    return result, audit


def audit_splits(frame: pd.DataFrame, assignments: pd.DataFrame) -> dict:
    if assignments.event_id.duplicated().any() or set(assignments.event_id) != set(frame.event_id):
        raise ValueError('Split membership mismatch')
    merged = frame.merge(assignments, on='event_id', validate='one_to_one')
    used = merged[merged.split != 'excluded']
    reasons = []
    if (used.groupby('group_id').split.nunique()>1).any(): reasons.append('GROUP_LEAKAGE')
    if (used.dropna(subset=['nearest_facility_id']).groupby('nearest_facility_id').split.nunique()>1).any(): reasons.append('FACILITY_LEAKAGE')
    labels = set(frame.label) if 'label' in frame else set()
    counts = {}
    for split in ('train','validation','test'):
        rows = used[used.split==split]
        counts[split] = len(rows)
        if rows.empty: reasons.append(f'EMPTY_{split.upper()}')
        if labels and set(rows.label) != labels: reasons.append(f'MISSING_CLASSES_{split.upper()}')
    return {'valid': not reasons, 'reasons': reasons, 'counts':counts,
            'excluded_count':int((merged.split=='excluded').sum()), 'group_count':int(assignments.group_id.nunique())}
