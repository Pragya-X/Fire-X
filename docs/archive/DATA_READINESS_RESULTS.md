# Data-readiness handoff — 2026-09-07

> Historical snapshot. Use [the documentation index](../README.md) for current guides. Recorded results and phase instructions below describe that earlier check.

**TRAINING BLOCKED.** Implemented the second attachment's immediate data-readiness
scope. The first attachment's Phase 8–11 training work did not proceed because
training_ready was false at entry, no Phase 7 outputs/usable labels were present,
and representative India data/reference inputs were absent. No gate was weakened,
no labels were assigned, and no project classifier was trained or integrated.

## Outcome

| Item | Actual result | Limitation |
|---|---|---|
| Multi-file India input support | CSV/Parquet loading, per-file schema checks, cross-file deduplication, lineage, hashes, dates, bounds, sensor metadata | User must supply actual exports and source/coverage records |
| Industrial reference support | Existing GIS engine + OSM export adapter; stable facility identity, explicit categories, geometry and tags; oil_gas explicitly supported in GeoJSON | Unknown tags are rejected, no guessed facility type; centers are not footprints |
| Land-cover support | Existing provider abstraction extended with local vector export; explicit category mapping/CRS/coverage | Real polygons and source coverage must be supplied; raster extraction not implemented |
| Bundle/provenance | Source/version/CRS per file; composite content hash includes all files; separate industrial/land-cover source metadata | Actual bundle absent; example config only |
| India event generation | **Not run: required real inputs absent** | No `thermal_events_india.parquet` was fabricated |
| Coverage/history/inspection | Working report CLI, per-feature coverage, null-history reasons, clustering review flags and deterministic member inspection | Reports do not establish representativeness or human approval |
| Training | **Blocked before and after execution** | No reviewed labels, credible reference/history coverage or India dataset |

## Tests run

- Focused legacy preprocessing/spatial/dataset regressions: 16 passed.
- New India metadata/reference/report tests: initially 10 passed, then 13 with
  land-cover/facility separation, changed reference hashes and chaining checks.
- Combined focused tests after refinements: 21 passed.
- Complete backend suite: **92 passed**, 2 existing dependency deprecation warnings.
  Run used temporary DATA_DIR/MODEL_DIR/SQLite paths and disabled SMTP.
- Frontend `npm run typecheck`: passed.
- Frontend `npm run build`: passed (20 static pages). Existing config skips linting.
- Corrected standalone startup tested on port 3101: started without the `next start`
  warning; `/login` and a `/_next/static/...css` asset both returned HTTP 200.
  Temporary test server stopped; user's server on port 3000 was not interrupted.
- Readiness CLI: executed for both missing India inputs and the current tutorial.
  Exit code **2 is intentional**, indicating TRAINING BLOCKED while writing reports.
- `git diff --check`: passed.
- No model training, evaluation, calibration, production integration or labeling.

## Generated reports

- `reports/ml/india_dataset_validation.json`
- `reports/ml/india_dataset_validation.md`
- `reports/ml/tutorial_dataset_validation.json`
- `reports/ml/tutorial_dataset_validation.md`
- `reports/ml/event_inspection_sample.csv`
- `reports/ml/event_inspection_sample.md`

The India report records missing clean/event/manifest/membership files. India
coverage is **not measurable**; it is not reported as 0% measured coverage.
The inspection sample explicitly names its current **tutorial** source.

## Current artifact inspection

Existing tutorial: 3 events / 5 NASA-published observations, all at
2025-06-06 00:01 UTC, African coordinates. Schema: thermal-events-v1, 69 columns.

| Event | Members | Mean FRP (MW) | Radius (km) | History |
|---|---:|---:|---:|---|
| EV-20bf71614d189656f3cf | 1 | 4.59 | effectively 0 | NO_PRIOR_OBSERVATIONS |
| EV-7f8e10c4709561819e0d | 2 | 0.92 | 0.164058 | NO_PRIOR_OBSERVATIONS |
| EV-31184afba9b3e686dbf5 | 2 | 1.52 | 0.085695 | NO_PRIOR_OBSERVATIONS |

Member records and FRP means were inspected against the report. Industrial context,
land-cover context and historical FRP baseline coverage are each **0/3** in this
excerpt. All source distances/overlaps are unavailable, not evidence that industry
or vegetation is absent. No chaining flags or nearby separate-event candidates
were found. There is no evidence here to recommend changing 1 km / 24 h defaults.
Independent human review remains PENDING; this inspection does not create labels.

## Readiness

| State | Existing tutorial | Requested India dataset |
|---|---|---|
| DATA_PIPELINE_READY | true: valid nonempty artifacts | false: inputs missing |
| REFERENCE_COVERAGE_READY | false | false |
| TEMPORAL_HISTORY_READY | false | false |
| LABELS_READY | false | false |
| TRAINING_READY | false | false |

No labels were supplied/assessed: industrial_fire=0, persistent_industrial_source=0,
wildfire=0, other=0, uncertain=0; A=0, B=0, C=0. These are **label counts**, not
predicted class counts. No industrial-fire precision/recall/F1, confusion matrix,
model comparison, feature importance or geographic generalization result exists.
No candidate is recommended for production; calibration is not the next task.

## Exact inputs and commands

Supply actual files, not the tutorial, at:

1. `data/input/firms/india/*.csv` (or explicit Parquet paths): latitude, longitude,
   acquisition_time or acq_date/acq_time; thermal, sensor and source fields retained.
2. `data/references/industrial.geojson`: stable facility IDs, explicit category,
   Point/Polygon/MultiPolygon geometry, source tags and actual CRS.
3. `data/references/landcover.geojson`: stable feature IDs, explicit
   forest/agriculture/urban/industrial category, real polygons and valid-data coverage.
4. `data/reference_bundle.json`: copy the provided `.example.json`, fill real
   source/version metadata and input CRS; paths resolve relative to the bundle.

Detailed schemas and coverage semantics are in `INDIA_DATA_READINESS.md`.
From the repository root, once those real inputs exist:

```sh
PYTHONPATH=backend .venv/bin/python -m app.ml.data.preprocessing \
  --input data/input/firms/india/*.csv --region india \
  --source 'REPLACE_WITH_REAL_NASA_EXPORT_SOURCE_AND_PRODUCT' \
  --raw-dir data/raw/firms/india \
  --output data/processed/firms_india_clean.parquet

PYTHONPATH=backend .venv/bin/python -m app.ml.build_dataset \
  --input data/processed/firms_india_clean.parquet \
  --reference-bundle data/reference_bundle.json \
  --output data/ml/thermal_events_india.parquet \
  --spatial-km 1 --temporal-hours 24 --history-radius-km 1

PYTHONPATH=backend .venv/bin/python -m app.ml.readiness \
  --events data/ml/thermal_events_india.parquet \
  --clean data/processed/firms_india_clean.parquet \
  --report-prefix reports/ml/india_dataset_validation \
  --inspection-prefix reports/ml/event_inspection_sample --sample-size 20
```

The last command already works without the data: it produces missing-input blockers.
It intentionally exits 2. This stage has no mechanism to turn training readiness true.

## Frontend startup follow-up

`npm start` now calls `scripts/start.mjs`, which copies static/public assets if
present and runs `.next/standalone/server.js`. This matches the existing standalone
build configuration. After stopping the current server, run from `frontend`:

```sh
npm run build
npm start
```

The npm audit inspection confirmed the two high-severity package findings are
Next.js and PostCSS. Npm proposed a major Next.js upgrade. No forced dependency
upgrade or script approval was performed; these findings remain a separate tested
migration task. The fsevents install-script notice did not prevent the verified
production startup. No claim is made that these advisories are fixed.

## Files changed in this stage

- `.gitignore`, `README.md`
- `backend/app/gis/engine.py`
- `backend/app/ml/data/preprocessing.py`
- `backend/app/ml/spatial_features.py`
- `backend/app/ml/build_dataset.py`
- `backend/app/ml/reference_bundle.py` (new)
- `backend/app/ml/readiness.py` (new)
- `backend/app/providers/osm.py`
- `backend/app/providers/landcover.py`
- `backend/tests/test_india_readiness.py` (new)
- `data/reference_bundle.example.json` (new config template, no observations)
- `data/references/README.md` (new)
- `docs/DATASETS.md`, `docs/ML_PIPELINE.md`
- `docs/INDIA_DATA_READINESS.md`, `docs/DATA_READINESS_RESULTS.md` (new)
- `frontend/package.json`, `frontend/scripts/start.mjs` (new startup helper)
- Generated reports listed above (inspection CSV is ignored by Git but exists locally).

## Next task / SIH progress

Supply representative India observations plus real reference/coverage files,
regenerate the dataset and inspect the report/sample before starting labeling.
This improves reproducible geospatial evidence preparation. It does not yet supply
trained-model evidence for industrial-vs-natural segregation or persistent-source
classification, and does not complete the SIH MVP requirements.
