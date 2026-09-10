"""Load, validate and archive FIRMS observations with row-level provenance.

Missing thermal measurements stay null; invalid supplied values are rejected.
Native sensor confidence is preserved. This pipeline never assigns source labels."""
from __future__ import annotations
import hashlib
import math
import re
import pandas as pd
import argparse
import json
import shutil
from typing import Any
from datetime import datetime, timezone
from pathlib import Path
from app.config import settings


REQUIRED = ('latitude', 'longitude')


def acquisition_datetime(row: dict) -> pd.Timestamp:
    if pd.notna(row.get('acquisition_time')):
        return pd.to_datetime(row['acquisition_time'], utc=True, errors='coerce')
    date, time = row.get('acq_date'), row.get('acq_time')
    if pd.isna(date) or pd.isna(time):
        return pd.NaT
    time = str(time).strip()
    if re.fullmatch(r'\d{1,4}\.0', time):
        time = time[:-2]
    if re.fullmatch(r'\d{1,4}', time):
        time = time.zfill(4)
        time = time[:2] + ':' + time[2:]
    if not re.fullmatch(r'\d{2}:\d{2}', time):
        return pd.NaT
    return pd.to_datetime(f'{date} {time}', format='%Y-%m-%d %H:%M', errors='coerce', utc=True)


def normalize_firms(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    df = frame.copy().reset_index(drop=True)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if df.columns.duplicated().any():
        raise ValueError('Duplicate column names after normalization')
    missing = [c for c in REQUIRED if c not in df]
    if 'acquisition_time' not in df:
        missing += [c for c in ('acq_date', 'acq_time') if c not in df]
    errors: list[list[str]] = [[] for _ in range(len(df))]
    for c in missing:
        for e in errors:
            e.append(f'missing_column:{c}')
    if 'brightness' not in df:
        df['brightness'] = None
    for alias in ('bright_ti4', 'brightness_ti'):
        if alias in df:
            df['brightness'] = df['brightness'].replace('', None).combine_first(df[alias])
    for col in ('latitude', 'longitude', 'frp', 'brightness'):
        original = df[col] if col in df else pd.Series(None, index=df.index, dtype=object)
        values = pd.to_numeric(original, errors='coerce').astype(float)
        for i, v in enumerate(values):
            absent = pd.isna(original.iloc[i]) or str(original.iloc[i]).strip() == ''
            bad = (not math.isfinite(v) and not absent)
            bad |= col in REQUIRED and not math.isfinite(v)
            bad |= col == 'latitude' and not -90 <= v <= 90
            bad |= col == 'longitude' and not -180 <= v <= 180
            bad |= col == 'frp' and v < 0
            bad |= col == 'brightness' and v <= 0
            if bad:
                errors[i].append(f'invalid:{col}')
        df[col] = values
    df['acquisition_time'] = pd.to_datetime([acquisition_datetime(r) for r in df.to_dict('records')], utc=True)
    for i in df.index[df.acquisition_time.isna()]:
        errors[i].append('invalid:acquisition_time')
    for col in ('satellite', 'instrument', 'confidence', 'daynight'):
        if col not in df:
            df[col] = None
    raw_daynight = df.daynight.copy()
    df['daynight'] = raw_daynight.astype('string').str.strip().str.upper().map({'D':'D','DAY':'D','N':'N','NIGHT':'N'})
    df['source_row'] = range(2, len(df) + 2)
    identity = ['latitude', 'longitude', 'acquisition_time', 'satellite', 'instrument']
    df['detection_id'] = [hashlib.sha256('|'.join('' if pd.isna(r[c]) else str(r[c]) for c in identity).encode()).hexdigest()[:24] for r in df.to_dict('records')]
    eligible = pd.Series([not e for e in errors], dtype=bool)
    duplicate = df.loc[eligible].duplicated(identity, keep='first')
    for i in duplicate.index[duplicate]:
        errors[i].append('duplicate_detection')
    valid = pd.Series([not e for e in errors], dtype=bool)
    rejected = frame.reset_index(drop=True).loc[~valid].copy()
    rejected['source_row'] = df.loc[~valid, 'source_row']
    rejected['validation_errors'] = [';'.join(errors[i]) for i in df.index[~valid]]
    clean = df.loc[valid].sort_values(['acquisition_time','detection_id']).reset_index(drop=True)
    report = {
        'input_rows': len(df), 'accepted_rows': len(clean), 'rejected_rows': len(rejected),
        'missing_columns': missing,
        'issues': [{'source_row': i+2, 'reasons': e} for i,e in enumerate(errors) if e],
        'missing_values': {c: int(clean[c].isna().sum()) for c in ('frp','brightness','daynight','satellite','instrument')},
        'unknown_daynight_rows': int((raw_daynight.notna() & df.daynight.isna()).sum()),
        'policy': 'Reject invalid coordinates/times/thermal values and duplicate detection identities; preserve missing optional values and native confidence. source_row is 1-based CSV line (header=1).',
    }
    return clean, rejected, report


def load_firms(path: str | Path) -> pd.DataFrame:
    """Read source files without losing leading-zero acquisition times."""
    path = Path(path)
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path, dtype=str)
    if path.suffix.lower() in ('.parquet', '.pq'):
        return pd.read_parquet(path)
    raise ValueError('FIRMS input must be CSV or Parquet')


def preprocess(input_path: Path | list[Path], output: Path, raw_dir: Path,
               source: str, *, region: str | None = None) -> dict:
    if not source.strip():
        raise ValueError('Source provenance is required')
    paths = sorted({Path(p).resolve() for p in (input_path if isinstance(input_path, list) else [input_path])})
    if not paths:
        raise ValueError('At least one input is required')
    # Inspect every input separately so a missing schema cannot be hidden by concatenation.
    frames, inputs, schema_errors = [], [], []
    raw_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        raw = raw_dir / f'{digest[:16]}_{path.name}'
        if path != raw.resolve():
            shutil.copyfile(path, raw)
        frame = load_firms(raw)
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        _, _, validation = normalize_firms(frame)
        if validation['missing_columns']:
            schema_errors.append({'path':str(path), 'missing_columns':validation['missing_columns']})
        frame['input_file'] = str(path)
        frame['input_row'] = range(2, len(frame)+2)
        frame['input_sha256'] = digest
        frames.append(frame)
        inputs.append({'path':str(path), 'raw_path':str(raw), 'sha256':digest, 'raw_row_count':len(frame)})
    combined = pd.concat(frames, ignore_index=True)
    clean, rejected, report = normalize_firms(combined)
    duplicate_count = sum('duplicate_detection' in issue['reasons'] for issue in report['issues'])
    coordinates = combined.reindex(columns=['latitude','longitude']).replace(r'^\s*$', None, regex=True)
    bounds = None if clean.empty else {
        'west':float(clean.longitude.min()), 'south':float(clean.latitude.min()),
        'east':float(clean.longitude.max()), 'north':float(clean.latitude.max())}
    date_range = None if clean.empty else {'start':clean.acquisition_time.min().isoformat(), 'end':clean.acquisition_time.max().isoformat()}
    digest = inputs[0]['sha256'] if len(inputs)==1 else hashlib.sha256(json.dumps(sorted(i['sha256'] for i in inputs)).encode()).hexdigest()
    report.update(source=source, input_sha256=digest, raw_path=inputs[0]['raw_path'] if len(inputs)==1 else None,
        inputs=inputs, schema_version='firms-v1', region_requested=region,
        raw_row_count=len(combined), valid_row_count=len(clean), duplicate_count=duplicate_count,
        missing_coordinate_count=int(coordinates.isna().any(axis=1).sum()),
        sensors={c:sorted(clean[c].dropna().astype(str).unique().tolist()) for c in ('satellite','instrument')},
        date_range=date_range, geographic_bounds=bounds,
        processing_timestamp=datetime.now(timezone.utc).isoformat(), input_schema_errors=schema_errors,
        representativeness='NOT_REVIEWED',
        india_envelope_note='67–98 E, 6–38 N is only an audit envelope; includes neighbors, not an India boundary or filter.',
        outside_india_envelope_count=int((~(clean.longitude.between(67,98) & clean.latitude.between(6,38))).sum()) if region=='india' else None)
    # Source-row refers to the combined input; input_file/input_row retain original lineage.
    for issue in report['issues']:
        origin = combined.iloc[issue['source_row']-2]
        issue.update(input_file=origin['input_file'], input_row=int(origin['input_row']))
    clean['data_source'] = source
    output.parent.mkdir(parents=True, exist_ok=True)
    rejected.to_csv(output.with_suffix('.rejected.csv'), index=False)
    report['clean_output_written'] = not bool(schema_errors)
    output.with_suffix('.validation.json').write_text(json.dumps(report, indent=2))
    if schema_errors:
        raise ValueError('Missing required schema in an input; no clean output written; see validation report')
    clean.to_parquet(output, index=False)
    report['clean_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.validation.json').write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, nargs='+', required=True)
    parser.add_argument('--region', choices=['india'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--raw-dir', type=Path)
    parser.add_argument('--source', required=True, help='Source URL/export provenance, or explicitly synthetic-test')
    args = parser.parse_args()
    output = args.output or Path(settings.DATA_DIR)/('processed/firms_india_clean.parquet' if args.region else 'processed/firms_clean.parquet')
    raw_dir = args.raw_dir or Path(settings.DATA_DIR)/('raw/firms/india' if args.region else 'raw/firms')
    print(json.dumps(preprocess(args.input, output, raw_dir, args.source, region=args.region), indent=2))


if __name__ == '__main__':
    main()
