# 36-hour hackathon MVP architecture refactor

This is a submission-architecture refactor, not a claim that the code was written in 36 hours. Existing uncommitted work and Git history were preserved.

## Analysis recorded before source edits

The initial analysis was delivered before consolidation. A complete AST import inventory and source snapshot were saved first; the detailed graph is retained in `reports/mvp-refactor/dependencies-before.json`. Static imports identify dependency edges, not measured runtime coverage.

The baseline was independently rerun: 140 backend tests, seven browser tests, TypeScript and the production build passed. Docker and psql executables were unavailable. Database, migrations and deployment behavior were therefore excluded from consolidation.

Current architecture: one FastAPI backend, one Next.js frontend, relational persistence, and offline preparation/review tooling. Safe candidates were adjacent FIRMS, event, inference and context/history modules. Configuration, database tables, GIS math, reviewed labels, splits and training guards were retained. No other dependency was proven removable.

Planned order: preprocessing → focused tests → event building → focused tests → event inference → focused tests → API grouping → schema comparison → documentation → full regression. The frontend already has meaningful page/component boundaries; no visual redesign or src-directory move was justified.

## Dependency map for every consolidation candidate

| Original module | Imported by (before) | Direct application dependencies | Tests / role |
|---|---|---|---|
| `backend/app/ml/data/validation.py` | `backend/app/ml/data/preprocessing.py`, `backend/app/providers/firms.py` | None | `test_event_clustering.py`, `test_event_dataset.py`, `test_firms_pipeline.py`, `test_india_readiness.py`; data correctness and readiness inputs |
| `backend/app/ml/data/preprocessing.py` | CLI/direct consumers only | `app.config`, `app.ml.data.validation` | `e2e_server.py`, `test_event_workspace.py`, `test_firms_pipeline.py`, `test_india_readiness.py`, `test_reviewed_training.py`; CLI-critical, lineage-critical |
| `backend/app/ml/event_clustering.py` | `backend/app/ml/build_dataset.py`, `backend/app/ml/datasets.py`, `backend/app/ml/readiness.py` | `app.gis.engine` | `test_event_clustering.py`; data correctness and readiness inputs |
| `backend/app/ml/build_dataset.py` | CLI/direct consumers only | `app.config`, `app.gis.engine`, `app.ml.datasets`, `app.ml.event_clustering`, `app.ml.reference_bundle`, `app.ml.spatial_features`, `app.services.temporal` | `e2e_server.py`, `test_event_dataset.py`, `test_event_workspace.py`, `test_india_readiness.py`, `test_reviewed_training.py`; CLI-critical, lineage-critical |
| `backend/app/ml/event_model.py` | `backend/app/ml/import_events.py`, `backend/app/routers/thermal_events.py` | `app.config`, `app.ml.reference_bundle`, `app.ml.training`, `app.services.event_intelligence` | `test_reviewed_training.py`; runtime inference, approval/readiness-critical |
| `backend/app/services/event_intelligence.py` | `backend/app/ml/anomaly.py`, `backend/app/ml/event_model.py` | `app.ml.normal_reviews`, `app.ml.training` | `test_reviewed_training.py`; runtime inference, approval/readiness-critical |
| `backend/app/routers/infrastructure.py` | `backend/app/main.py` | `app.database`, `app.gis.engine`, `app.models`, `app.providers.osm` | `test_api.py` via registered HTTP routes; browser regression suite; runtime-critical |
| `backend/app/routers/industrial_zones.py` | `backend/app/main.py` | `app.database`, `app.gis.engine`, `app.models`, `app.schemas` | `test_api.py` via registered HTTP routes; browser regression suite; runtime-critical |
| `backend/app/routers/satellite.py` | `backend/app/main.py` | `app.database`, `app.models` | `test_api.py` via registered HTTP routes; browser regression suite; runtime-critical |
| `backend/app/routers/historical.py` | `backend/app/main.py` | `app.database`, `app.models` | `test_api.py` via registered HTTP routes; browser regression suite; runtime-critical |
| `backend/app/routers/analytics.py` | `backend/app/main.py` | `app.database`, `app.models`, `app.utils.helpers` | `test_api.py` via registered HTTP routes; browser regression suite; runtime-critical |

External imports, conditional imports and all noncandidate modules are also included in the saved graph. Before editing each group, source and test consumers were inspected. The route candidates have no direct application consumers beyond main.py; their API contracts remain the stable interface.

### Criticality and merge decision

“Indirect” means a caller depends on the module, not that the module exposes a standalone command. All candidates were merged only after mapping these edges.

| Original candidate | Runtime critical | CLI critical | Readiness critical | Decision |
|---|---|---|---|---|
| data/validation | Yes: FIRMS provider | Indirect preprocessing | Input correctness | Merge into preprocessing |
| data/preprocessing | Yes: FIRMS normalization | Yes: preserve command | Provenance/clean input | Retain as destination |
| event_clustering | Indirect import workflow | Indirect build/readiness | Event identities/membership | Merge; schema constants retain values |
| build_dataset | Indirect import workflow | Yes: preserve command | Features and artifact lineage | Retain as destination |
| event_model | Yes: event API/import | Indirect import workflow | Approval calls check_gate | Merge functions unchanged |
| event_intelligence | Yes: inference | Optional anomaly command imports class | Approval and normal-review gates | Retain destination and class identity |
| infrastructure routes | Yes | No | No | Merge context handlers |
| industrial_zones routes | Yes | No | No | Merge context handlers |
| satellite routes | Yes | No | No | Merge context handlers |
| historical routes | Yes | No | No | Merge analytics handlers |
| analytics routes | Yes | No | No | Retain as destination |

## Before

```text
backend/app/
  ml/data/preprocessing.py + validation.py
  ml/event_clustering.py + build_dataset.py
  ml/event_model.py
  services/event_intelligence.py
  routers/infrastructure.py, industrial_zones.py, satellite.py
  routers/analytics.py, historical.py
  gis/engine.py; separate schema/review/split/training modules
frontend/app/, components/, lib/, hooks/
docs/  current guides mixed with eight historical reports
```

## After

```text
backend/app/
  ml/data/preprocessing.py       Load, normalize, validate, archive
  ml/build_dataset.py            Cluster, enrich, calculate history, save
  ml/datasets.py                 Shared event schema and validation
  services/event_intelligence.py Approve/load model, decide, explain
  routers/context.py            Facility, zone and satellite reads
  routers/analytics.py          Statistics and history
  gis/engine.py                  Existing spatial calculations
  ml/                           Preserved review, readiness and offline tools
  database.py, models.py, event_models.py  Unchanged persistence
frontend/app/, components/, lib/, hooks/  Unchanged UI structure
docs/                           Current guides
docs/archive/                   Historical engineering reports
```

## File reduction

Files before: **197**. Files after: **193**. Net reduction: **4**.

Backend application Python files: **69 → 63**.

- Files removed: **7** absorbed source modules; no feature or test deleted.
- Files merged: **11 original modules into five destinations**, four existing destinations and one new file.
- Files moved: **eight historical documents** into archive/.
- New documentation files: archive/README.md and this report.

Counts use unique existing Git-tracked or nonignored project text source/configuration/documentation paths, including tests, package initializers, manifests and input templates. They exclude reports, dependencies, caches, build output, Git internals, generated next-env.d.ts, screenshots, icons and observation CSVs. Complete before/after path inventories are saved with the local evidence.

## Actual merge map and removed code

| Original files under backend/app | Destination | Reason |
|---|---|---|
| `ml/data/validation.py + ml/data/preprocessing.py` | `ml/data/preprocessing.py` | Same input contract; loading and rejection logic now share the stable preprocessing CLI. |
| `ml/event_clustering.py + ml/build_dataset.py` | `ml/build_dataset.py` | Clustering and feature assembly form one event-building workflow. EVENT_COLUMNS moves unchanged into the existing datasets.py schema, avoiding a cycle. |
| `ml/event_model.py + services/event_intelligence.py` | `services/event_intelligence.py` | Model approval, evidence decisions and explanations are one inference path. The existing anomaly class module identity stays intact. |
| `routers/infrastructure.py + routers/industrial_zones.py + routers/satellite.py` | `routers/context.py` | Small read-only context routes share database and geometry dependencies; endpoint URLs and tags are preserved. |
| `routers/historical.py + routers/analytics.py` | `routers/analytics.py` | History and dashboard statistics query the same legacy observation store. No HTTP handler behavior changes. |

An additional unreferenced `analytics 2.py` appeared during verification and was byte-identical to the original analytics module. Its contents were preserved in the ignored `reports/mvp-refactor/recovered/` directory; it is not treated as an extra baseline source reduction. Its origin was not established.

Removed source paths:
- `backend/app/ml/data/validation.py`
- `backend/app/ml/event_clustering.py`
- `backend/app/ml/event_model.py`
- `backend/app/routers/historical.py`
- `backend/app/routers/industrial_zones.py`
- `backend/app/routers/infrastructure.py`
- `backend/app/routers/satellite.py`

The removed files contained absorbed implementations, not dead features. No compatibility shims were necessary: existing preprocessing/build/readiness CLI module names remain; internal imports and active documentation were updated together. Historical reports intentionally retain descriptions of their original source paths.

## Preserved boundaries and decisions

- GIS was already one 227-line calculation module. Event-specific features and provenance-aware reference validation remain separate responsibilities.
- Shared EVENT_COLUMNS now belongs to the existing dataset schema. Column values/order and validation policy did not change.
- Classification rules and model-approval functions keep their original function bodies. The anomaly class remains at app.services.event_intelligence.HistoricalAnomalyModel for serialization compatibility.
- Label review, readiness, temporal/spatial leakage controls and training gates remain distinct and unchanged. Ten key gate/database/configuration/GIS files are byte-identical to baseline.
- No database schema, migration, Compose, Dockerfile or frontend runtime code changed. Docker/PostGIS changes were stopped because this environment cannot verify them.
- Kept backend/.env → config.py and frontend/.env.local as the existing configuration paths. Root duplicates or extra entry scripts would add ambiguity.
- Existing data inbox/raw/derived/tutorial paths and separate demo databases remain. No artifacts were relocated or relabeled.
- No package was removed or upgraded. Dependencies serve runtime, serialization, optional providers or tests; a text-search absence alone was not treated as proof of non-use. The existing development requirements already provide one installation command.
- Moved eight historical reports with mechanical Markdown-link rebasing only; prose, timestamps, measurements and attribution remain unchanged. Current guide links and the report helper were repaired.

## Validation

| Check | Before | After |
|---|---|---|
| Backend | PASS — 140 tests | PASS — 140 tests |
| Browser | PASS — 7 tests | PASS — 7 tests |
| TypeScript | PASS | PASS |
| Production frontend build | PASS | PASS — 21 static pages; lint remains skipped |
| Docker | NOT RUN — tool unavailable | NOT RUN — unchanged configuration |
| Native PostGIS | NOT RUN — runtime/client unavailable | NOT RUN — schema and migration unchanged |

Focused checks passed after each group: preprocessing 21; event construction/GIS/history 29; inference/review 33; API/production guards 46. The first route edit briefly removed the analytics destination while absorbing the old file; collection failed. It was restored from the pre-edit source, then the focused and full suites passed. This failed attempt is not counted as passing.

Both 61-operation non-demo and 65-operation demo OpenAPI schemas match the baseline exactly. CLI --help checks pass for preprocessing, build_dataset and readiness. Twenty scientific function/class definitions match the baseline AST after ignoring imports. Existing tests retain their assertions; only imports changed where necessary. No coverage percentage was measured.

The browser suite uses isolated fixtures and the published NASA tutorial excerpt; its Unknown draft is disposable test data, not a generated training label. Live services, security certification and real model performance were not tested. Two existing Python dependency deprecation warnings remain.

## ML status

```text
Models trained: NO
Labels generated: NO (no project labels; existing isolated test fixtures remain)
training_ready: false
```

Representative India observations, industrial/land-cover coverage and independent reviewed labels remain unavailable. The existing saved readiness record remains blocked; no gate requirement was weakened. Optional learned tooling is implemented but unvalidated, not a completed project model.

## Remaining limitations

Real-data coverage and reviewed ground truth are missing. Native deployment, public-route authorization, dependency security work and broader accessibility/load/recovery verification remain outstanding. Legacy dashboard and reviewed-event data contracts differ and are kept separate deliberately. Pixel-based satellite confirmation and calibrated model confidence are future work.

## Exactly one next engineering task

**Verify the existing Docker/PostGIS deployment on a machine with Docker available**, including migration execution and read-only database health checks, without changing the data-readiness gate.

## Two-minute architecture question

**YES, as a design assessment:** the README maps the complete main path to six responsibilities and links directly to their implementations. A timed judge walkthrough has not been conducted. Detailed review/approval safeguards and optional experiments remain available behind that short explanation.
