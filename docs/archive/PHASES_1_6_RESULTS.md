# Phase 1–6 handoff — SIH 26162

> Historical snapshot. Use [the documentation index](../README.md) for current guides. Recorded results and phase instructions below describe that earlier check.

Scope completed: incremental data/feature pipeline implementation. Stopped before
Phase 7 labeling and all project-model training. This is not completion of the
full SIH MVP: no validated real classifier or held-out performance exists.

| Requirement | Status | Implementation evidence | How tested | Remaining limitation |
|---|---|---|---|---|
| 1. Explicit ML modes | Implemented | config, predict, classification service, ML/status/system APIs, AI Intelligence UI | Rule/demo/missing/corrupt/schema/fallback tests; API provenance persistence; frontend build | Real trained artifacts absent; event-to-real-model integration deferred to Phase 17 |
| 2. FIRMS preprocessing | Implemented | ml/data loader, validator, preprocessing CLI; provider shares validator | Invalid/missing/duplicate/VIIRS/mixed-sensor/provider-error tests; real published NASA excerpt CLI | Only five published example observations available; no fresh live API download or broad India archive |
| 3. Thermal event clustering | Implemented | event_clustering.py; membership Parquet | Spatial/time separation, dateline, singletons, shuffled rows, equivalent numeric config | Connectivity can chain; parameters are MVP engineering choices |
| 4. Expanded GIS features | Implemented where source data permits | GIS engine, spatial_features.py, explicit reference importer | High-latitude nearest ranking, metric CRS import, polygon boundaries/holes, footprint distance, empty context | Actual reference layers/coverage absent in delivered sample; fractions remain null |
| 5. Expanded temporal features | Implemented | services/temporal.py; live service and dataset integration | Past-only windows, spatial exclusion, zero baseline/variance, burst vs daily recurrence, long current event | Observed counts do not establish sensor coverage; persistence remains heuristic |
| 6. Unlabeled event builder | Implemented | build_dataset.py, datasets.py; 69-column schema + manifest | Deterministic Parquet roundtrip, no-label requirement, nulls, input validation, membership conservation; CLI sample | Not training-ready; labeling and representative real data still needed |

## Tests and execution

Focused tests ran after each phase, followed by final regression:

- Phase 1: classification + mode tests — 10 passed initially.
- Phase 2: preprocessing + mode tests — 8 passed initially.
- Phase 3: event clustering — 3 passed initially.
- Phase 4: expanded spatial + existing GIS — 7 passed initially.
- Phase 5: expanded temporal + existing temporal/classification — 16 passed initially.
- Phase 6: dataset tests — 3 passed after fixing a schema-validator predicate
  that accidentally matched `duration` as a proportion.
- Final backend suite after added edge-case regressions: **79 passed**, 2 existing
  dependency deprecation warnings (Starlette/AnyIO and ReportLab/AST).
- `npm run typecheck`: passed.
- `npm run build`: passed; 20 static pages generated. Existing Next configuration
  skips linting. There is no existing frontend browser-test runner; no interactive
  browser/dashboard acceptance test was performed.
- `git diff --check`: passed.
- Real published NASA excerpt preprocessing: 5 accepted, 0 rejected.
- Event CLI and dataset validation: 3 events, 5 detection memberships, 69 columns.
- No project model training or held-out evaluation was run, as requested. Small
  DummyClassifier artifacts are used only inside temporary unit tests.
- Docker startup: not run, Docker executable unavailable. Existing Compose also
  requires a PostgreSQL driver not currently listed; full deployment audit deferred.

The backend acceptance run used an isolated test SQLite database, temporary
`DATA_DIR` and `MODEL_DIR`, and empty SMTP settings. No external messages sent.

## Generated outputs

Under repository root (ignored generated data remain available locally):

- `data/raw/firms/96b08e437d663d74_firms_nasa_tutorial.csv` — exact raw input copy.
- `data/processed/firms_clean.parquet` — 5 accepted observations.
- `data/processed/firms_clean.validation.json` — validation/provenance/hash.
- `data/processed/firms_clean.rejected.csv` — header-only, zero rejections.
- `data/ml/thermal_events.parquet` — 3 events, member counts 1/2/2.
- `data/ml/thermal_events.membership.parquet` — detection-to-event lineage.
- `data/ml/thermal_events.manifest.json` — configuration, sources, hashes, null counts.
- `data/ml/thermal_events.schema.json` — versioned column types/units.

The source CSV is a documented transcription of NASA's five published VIIRS
observations from June 6, 2025 in Africa. It is not an India dataset, a full archive,
or an independently retrieved fresh observation batch. Mean event FRPs are 4.59,
0.92 and 1.52 MW. No source labels are inferred. Spatial features and historical
thermal baselines are null; all event persistence scores are zero. The sample
therefore validates data plumbing, not industrial-fire discrimination.

## Exact commands

From `/Users/chandankumarmahato/Desktop/SIH2026`, using the created `.venv`:

```sh
PYTHONPATH=backend .venv/bin/python -m app.ml.data.preprocessing \
  --input data/samples/firms_nasa_tutorial.csv \
  --source https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html
PYTHONPATH=backend .venv/bin/python -m app.ml.build_dataset \
  --input data/processed/firms_clean.parquet \
  --output data/ml/thermal_events.parquet \
  --spatial-km 1 --temporal-hours 24 --history-radius-km 1
```

Use `--references`, `--reference-source` and `--reference-crs` to enrich from actual
reference layers, as documented in ML_PIPELINE.md and DATASETS.md. Replace the
sample with a real India export and enough historical coverage before labeling.

## Unresolved / deferred

- Representative real India observations, historical coverage, actual OSM
  footprints/land-cover data and reviewed labels are not supplied.
- Current application live ingestion still uses seeded GIS context; the new
  offline event builder only uses explicitly supplied context. Integrating event
  persistence, new map overlays and production reference ingestion is later scope.
- The new event data is separate from legacy hotspot inference. The real-model
  feature adapter, training, calibration and evaluation remain unimplemented.
- Existing satellite provider fabricates some validation measurements on its
  live path. The event builder does not use those fields; fix before claiming
  real satellite validation in a later phase.
- Existing database geometry is WKT text, not native indexed PostGIS geometry.
- Npm install reported two high-severity dependency advisories. Dependency/security
  remediation and Docker/Compose corrections are deferred to the requested later
  deployment audit; no dependency versions were changed outside Parquet/CRS needs.
- Dense space/time neighborhoods can be expensive, chain incidents together,
  and require domain-specific threshold review. Large geographic reference
  polygons require clipping for local projected geometry operations.

Recommended next phase: inspect an adequately sourced India event dataset and
reference coverage, then **Phase 7 — labeling schema/workflow**. Do not train until
that inspection and label-quality review are complete.

## Files changed
- `.gitignore`
- `README.md`
- `backend/.env.example`
- `backend/app/config.py`
- `backend/app/gis/engine.py`
- `backend/app/ml/build_dataset.py`
- `backend/app/ml/data/__init__.py`
- `backend/app/ml/data/firms_loader.py`
- `backend/app/ml/data/preprocessing.py`
- `backend/app/ml/data/validation.py`
- `backend/app/ml/datasets.py`
- `backend/app/ml/event_clustering.py`
- `backend/app/ml/predict.py`
- `backend/app/ml/spatial_features.py`
- `backend/app/ml/train_model.py`
- `backend/app/providers/firms.py`
- `backend/app/routers/ingest.py`
- `backend/app/routers/ml.py`
- `backend/app/routers/system.py`
- `backend/app/schemas.py`
- `backend/app/services/classification_service.py`
- `backend/app/services/temporal.py`
- `backend/requirements.txt`
- `backend/tests/test_api.py`
- `backend/tests/test_event_clustering.py`
- `backend/tests/test_event_dataset.py`
- `backend/tests/test_event_spatial.py`
- `backend/tests/test_event_temporal.py`
- `backend/tests/test_firms_pipeline.py`
- `backend/tests/test_ml_modes.py`
- `data/samples/README.md`
- `data/samples/firms_nasa_tutorial.csv`
- `docs/DATASETS.md`
- `docs/ML_PIPELINE.md`
- `docs/PHASES_1_6_AUDIT.md`
- `docs/PHASES_1_6_RESULTS.md`
- `frontend/app/(app)/ai-intelligence/page.tsx`
- `frontend/lib/api.ts`
