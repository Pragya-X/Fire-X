"""Temporal analysis of repeated detections.

Distinguishes persistent operational heat sources (steady, high cadence) from
sudden abnormal fires (isolated high-intensity detections) and recurring /
intermittent behaviour. Produces a persistence score (0-100) that feeds the
classifier and the risk engine.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional


def _gap_stats(detections: list[datetime]) -> Optional[dict]:
    if len(detections) < 2:
        return None
    gaps = [(b - a).total_seconds() / 3600.0 for a, b in zip(detections, detections[1:])]
    mean = sum(gaps) / len(gaps)
    var = sum((g - mean) ** 2 for g in gaps) / len(gaps)
    return {
        "gaps_hours": [round(g, 1) for g in gaps],
        "mean_gap_hours": mean,
        "std_gap_hours": var**0.5,
    }


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def analyze_detections(
    detections: list[datetime],
    window_days: int = 14,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Analyse a sorted list of detection datetimes (oldest first).

    Accepts naive and aware datetimes (SQLite returns naive) and normalises
    everything to UTC.
    """
    now = _as_utc(now or datetime.now(timezone.utc))
    if window_days <= 0:
        raise ValueError("window_days must be positive")
    dets = sorted({_as_utc(d) for d in detections if now - timedelta(days=window_days) <= _as_utc(d) <= now})
    n = len(dets)

    if n == 0:
        return {
            "pattern": "unknown",
            "persistence_score": 0.0,
            "n_detections": 0,
            "days_span": 0,
            "mean_gap_hours": 0.0,
            "std_gap_hours": 0.0,
            "timeline": [],
        }

    span_days = max(1.0, (dets[-1] - dets[0]).total_seconds() / 86400.0)
    gaps = _gap_stats(dets)
    mean_gap = gaps["mean_gap_hours"] if gaps else 0.0
    std_gap = gaps["std_gap_hours"] if gaps else 0.0

    # --- persistence score ---
    persistence = 0.0
    if n == 1:
        persistence = 0.0
    elif n >= 2:
        cadence = 14.0 / window_days  # baseline
        coverage = min(1.0, (n * mean_gap / 24.0) / window_days) if mean_gap > 0 else 0.0
        regularity = 1.0 if gaps and gaps["mean_gap_hours"] > 0 else 0.0
        if gaps and gaps["mean_gap_hours"] > 0:
            cv = gaps["std_gap_hours"] / max(gaps["mean_gap_hours"], 1e-9)
            regularity = max(0.0, 1.0 - min(1.0, cv / 1.2))
        persistence = min(
            100.0,
            (len({d.date() for d in dets}) * 6.0) + regularity * 25.0 + coverage * 15.0,
        )

    # --- pattern ---
    pattern = "unknown"
    if n == 1:
        age_hours = (now - dets[0]).total_seconds() / 3600.0
        pattern = "sudden" if age_hours < 72 else "unknown"
    elif n >= 2:
        if persistence >= 50 and mean_gap <= 36 and std_gap <= 24:
            pattern = "persistent"
        elif persistence >= 50:
            pattern = "persistent" if n >= 5 else "recurring"
        elif n <= 3:
            pattern = "sudden" if span_days <= 2 else "intermittent"
        else:
            # cluster detection: gaps with big jumps indicate recurring bursts
            if gaps and gaps["mean_gap_hours"] > 48:
                pattern = "recurring"
            else:
                pattern = "intermittent"

    # --- timeline: detection flags per day over the window ---
    start = dets[-1] - timedelta(days=window_days)
    timeline: list[dict] = []
    day = start
    while day <= dets[-1] + timedelta(days=1):
        day_dets = [d for d in dets if day <= d < day + timedelta(days=1)]
        timeline.append(
            {
                "date": day.date().isoformat(),
                "detected": len(day_dets) > 0,
                "count": len(day_dets),
            }
        )
        day += timedelta(days=1)

    return {
        "pattern": pattern,
        "persistence_score": round(persistence, 1),
        "n_detections": n,
        "days_span": round(span_days, 1),
        "mean_gap_hours": round(mean_gap, 1),
        "std_gap_hours": round(std_gap, 1),
        "timeline": timeline,
    }

def historical_features(
    records: list[dict], *, reference_time: datetime, current_frp: float | None = None,
    latitude: float | None = None, longitude: float | None = None,
    radius_km: float = 1.0,
) -> dict[str, Any]:
    """Past-only 90-day statistics. Never include observations at/after event start.

    Counts mean observed detections, not continuous coverage. Standard deviations
    use population convention. Zero-variance z scores and zero-denominator ratios
    are unavailable. Location variance is mean squared radial distance (km²).
    """
    import math
    import statistics
    from app.gis.engine import haversine_km, validate_coordinates
    if not math.isfinite(radius_km) or radius_km <= 0:
        raise ValueError('radius_km must be positive')
    if (latitude is None) != (longitude is None):
        raise ValueError('Both latitude and longitude are required')
    if latitude is not None:
        validate_coordinates(latitude, longitude)
    now = _as_utc(reference_time)
    past = []
    seen = set()
    for record in records:
        stamp = record.get('acquisition_time', record.get('detection_time'))
        if stamp is None:
            continue
        if isinstance(stamp, str):
            stamp = datetime.fromisoformat(stamp.replace('Z','+00:00'))
        stamp = _as_utc(stamp)
        if not now-timedelta(days=90) <= stamp < now:
            continue
        lat, lon = record.get('latitude'), record.get('longitude')
        radial = None
        if latitude is not None:
            if lat is None or lon is None:
                continue  # Cannot establish membership in a spatial neighborhood.
            radial = haversine_km(latitude,longitude,float(lat),float(lon))
            if radial > radius_km:
                continue
        identity = record.get('detection_id') or (stamp,lat,lon,record.get('satellite'),record.get('instrument'))
        if identity in seen:
            continue
        seen.add(identity)
        past.append({**record,'time':stamp,'radial_km':radial})
    past.sort(key=lambda r:r['time'])
    result: dict[str, Any] = {}
    for days, suffix in ((1,'24h'),(7,'7d'),(30,'30d'),(90,'90d')):
        window = [r for r in past if r['time'] >= now-timedelta(days=days)]
        result[f'detections_{suffix}'] = len(window)
        if days>1:
            result[f'active_days_{suffix}'] = len({r['time'].date() for r in window})

    def numeric(field: str) -> list[float]:
        return [float(r[field]) for r in past if r.get(field) is not None and math.isfinite(float(r[field]))]

    frps, brightness = numeric('frp'), numeric('brightness')
    mean = statistics.mean(frps) if frps else None
    std = statistics.pstdev(frps) if frps else None
    current = current_frp if current_frp is not None and math.isfinite(current_frp) else None
    delta = current-mean if current is not None and mean is not None else None
    gaps = [(b['time']-a['time']).total_seconds()/3600 for a,b in zip(past,past[1:])]
    radial = [r['radial_km'] for r in past if r['radial_km'] is not None]
    result.update(
        time_since_previous_detection=(now-past[-1]['time']).total_seconds()/3600 if past else None,
        historical_mean_frp=mean, historical_median_frp=statistics.median(frps) if frps else None,
        historical_std_frp=std, historical_max_frp=max(frps) if frps else None,
        frp_delta_from_baseline=delta,
        frp_ratio_to_baseline=current/mean if current is not None and mean is not None and mean>0 else None,
        frp_z_score=delta/std if delta is not None and std is not None and std>0 else None,
        historical_mean_brightness=statistics.mean(brightness) if brightness else None,
        mean_detection_interval_hours=statistics.mean(gaps) if gaps else None,
        std_detection_interval_hours=statistics.pstdev(gaps) if gaps else None,
        same_location_recurrence=len({r['time'].date() for r in past})/90,
        spatial_location_variance=statistics.mean([d*d for d in radial]) if radial else None,
        day_ratio=sum(isinstance(r.get('daynight'), str) and r['daynight']=='D' for r in past)/len(past) if past else None,
        night_ratio=sum(isinstance(r.get('daynight'), str) and r['daynight']=='N' for r in past)/len(past) if past else None,
        history_start= (now-timedelta(days=90)).isoformat(), history_end_exclusive=now.isoformat(),
    )
    return result
