# Recorded project evidence

Saved engineering evidence; not a new validation run or official SIH assessment

This helper reads local reports without running tests or training. Input hashes and timestamps are recorded in `reports/sih_readiness.json`. Missing evidence remains unavailable. A file's existence does not establish a validated implementation.

## Recorded checks

- backend: `{"errors": 0, "failures": 0, "skipped": 0, "tests": 140}`
- browser: `{"duration": 5047.812, "expected": 7, "flaky": 0, "skipped": 0, "startTime": "2026-09-08T23:33:51.923Z", "unexpected": 0}`
- readiness: `{"blockers": ["CLUSTERING_NOT_REVIEWED", "EMPTY_OR_NON_INDIA_TRAINING_DATA", "MINIMUM_CLASS_SUPPORT_NOT_MET", "NO_ELIGIBLE_REVIEWED_LABELS", "NO_REFERENCE_BUNDLE", "NO_TRAINABLE_FEATURES", "REFERENCES_NOT_REVIEWED", "REPRESENTATIVENESS_NOT_REVIEWED", "SPLIT_VALIDATION_FAILED", "TEMPORAL_HISTORY_NOT_REVIEWED"], "status": "recorded", "training_ready": false}`

Frontend build/typecheck, native PostGIS, containers, real-model evaluation and security status must be established separately. No grade or readiness percentage is calculated.

## Implementation and remaining work

| Area | Implementation | Evidence to inspect | Remaining limitation |
|---|---|---|---|
| India data pipeline | `backend/app/ml/data/preprocessing.py`; `backend/app/ml/reference_audit.py` | test_firms_pipeline.py; test_reference_extensions.py | Real representative India collection and reviewed coverage missing |
| Reference data | `backend/app/ml/reference_bundle.py`; `backend/app/ml/spatial_features.py` | test_india_readiness.py; test_reference_extensions.py | Real source versions/coverage missing; raster conversion and relation assembly remain upstream |
| Labeling system | `backend/app/ml/labels.py`; `backend/app/routers/thermal_events.py` | test_reviewed_training.py; test_event_workspace.py; browser workflow | Workflow verified; no real labels supplied |
| Training dataset | `backend/app/ml/training.py` | reports/ml/training_readiness.json | Zero eligible rows; real dataset and label quality still unassessed |
| Leakage-safe splitting | `backend/app/ml/splits.py` | test_reviewed_training.py | Grouping/purge guards tested; real collection still requires overlap and split review |
| Model training | `backend/app/ml/training.py` — uses optimized `HistGradientBoostingClassifier` (histogram-based gradient boosting) instead of iterative Random Forest for efficient inference | test_blocked_training_never_fits | Real training blocked; optional boosters not installed/run |
| Model evaluation | `backend/app/ml/evaluation.py` | test_metric_values_are_computed_and_absent_class_is_unavailable; test_reliability_bins_cover_extremes_and_edges | Metric arithmetic tested; no project performance, intervals or external benchmark |
| Explainability | `backend/app/services/event_intelligence.py` | test_event_model_never_loads_unapproved_artifact; explanation API test | No approved model/SHAP library; real attribution path unexecuted |
| Anomaly detection | `backend/app/ml/anomaly.py`; `backend/app/ml/normal_reviews.py`; `backend/app/services/event_intelligence.py` | statistical anomaly and normal-review tests | Learned anomaly fitting/evaluation/deployment unavailable |
| Persistent source engine | `backend/app/services/event_intelligence.py`; `backend/app/services/temporal.py` | test_event_temporal.py; test_anomaly_no_baseline_and_zero_variance_are_unknown | Recurrence/stability heuristics are not validated source identification |
| Hybrid decision engine | `backend/app/services/event_intelligence.py` | hybrid unit tests and Unknown API/browser tests | Classifier integration tooling exists; no real validation or learned-anomaly deployment |
| GIS database | `backend/app/event_models.py`; `backend/app/ml/import_events.py`; `backend/migrations/001_event_postgis.sql` | SQLite import/API integration; native SQL inspection | PostGIS server/migration/index execution and scale tests not run |
| Frontend | `frontend/app/(app)/event-workspace/page.tsx`; `frontend/components/map/event-map.tsx` | Production build; typecheck; Playwright regression tests | Tiles/live imagery and trained-model panels not empirically validated |
| Deployment and security | `docker-compose.production.yml`; `backend/Dockerfile`; `frontend/Dockerfile`; `backend/app/config.py` | test_production_configuration.py; auth regression tests; reports/npm_audit.json | Earlier npm audit findings; Docker/PostGIS/TLS/load/operational hardening incomplete |
| Testing | `backend/tests`; `frontend/tests/e2e` | reports/backend_tests.xml; reports/backend_coverage.json; reports/frontend_tests.json | Partial coverage; external providers, optional ML, PostGIS and load tests outstanding |
| SIH demo | `docs/SIH_DEMO_GUIDE.md` | Five explicit scenario walkthroughs and live Unknown review test | Only scripted/Unknown demonstrations; no five real independently verified cases |
| Documentation | `docs/ARCHITECTURE.md`; `docs/REVIEWED_ML_PIPELINE.md`; `docs/DEPLOYMENT_GUIDE.md`; `docs/API_EVENT_REFERENCE.md`; `docs/DEVELOPER_GUIDE.md`; `docs/SIH_DEMO_GUIDE.md` | Source-linked documentation and reports/openapi.json | Needs deployment-specific runbooks and official SIH rubric mapping |
| SIH evidence check | `scripts/build_sih_report.py` | reports/sih_readiness.json; docs/SIH_READINESS_REPORT.md | Checklist is internal; no official judging result or certification |

Use [the input checklist](REAL_DATA_INPUT_CHECKLIST.md) for missing datasets and [the roadmap](ROADMAP.md) for next steps. Historical evidence does not establish current scientific performance.
