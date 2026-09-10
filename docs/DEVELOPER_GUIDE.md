# Developer guide

Use the root [README](../README.md) for installation. Use [architecture](ARCHITECTURE.md) to locate responsibilities and [API.md](API.md) for every endpoint. Avoid adding another API or service when an existing function can do the job.

## Running checks

From the repository root with `.venv` active:

```sh
python -m pytest backend/tests -q
```

`backend/tests/conftest.py` configures a temporary data directory before test modules import the application. Databases, generated demo files, model paths, uploads and the email outbox stay there. Provider credentials are cleared for tests. The directory is removed after the run; test data must never enter the real-data inbox.

For coverage (reports stay in your working directory):

```sh
python -m pytest backend/tests -q --cov=app --cov-branch --cov-report=term-missing
```

Install `backend/requirements-dev.txt` first. Coverage reports describe exercised code, not geographic coverage or model performance. Assertions about metric arithmetic use explicit test arrays; no real model fitting occurs.

From `frontend`:

```sh
npm ci
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Playwright starts the built standalone frontend on 3101 and an isolated FastAPI server on 8101. Both ports must be free. The backend creates a temporary SQLite store from the documented NASA tutorial excerpt. Browser tests intercept external tiles; contract tests also use explicit UI fixtures. One integration test uses actual HTTP handlers and saves an Unknown draft. Credentials in those tests belong only to disposable databases.

No live NASA/Planet service, trained model or native PostGIS is validated by these checks. The production build skips linting in the existing Next configuration. A working lint setup is tracked as technical debt.

## Test groups

Tests remain in their existing files so historical commands and imports continue to work.

| Group | Files under `backend/tests/` |
|---|---|
| Legacy API and rules | `test_api.py`, `test_classification.py`, `test_risk.py`, `test_temporal.py`, `test_gis.py` |
| Observations and events | `test_firms_pipeline.py`, `test_event_clustering.py`, `test_event_dataset.py`, `test_event_spatial.py`, `test_event_temporal.py` |
| References and readiness | `test_india_readiness.py`, `test_reference_extensions.py` |
| Model modes and reviews | `test_ml_modes.py`, `test_reviewed_training.py` |
| Workspace and production guards | `test_event_workspace.py`, `test_production_configuration.py` |
| Notification delivery contracts | `test_notifications.py` (email intercepted, database/SSE behavior checked) |

For example: `python -m pytest backend/tests/test_firms_pipeline.py backend/tests/test_india_readiness.py -q`.

Frontend contract/navigation/settings checks are in `frontend/tests/e2e/event-workspace.spec.ts`; the disposable real-API workflow is in `live-api.spec.ts`. The extra settings test verifies actual navigation and provider status rather than pretending saved browser preferences affect the server.

Mode tests check both fresh-process OpenAPI registration and rejection of demo requests after disabling demo mode. Browser checks cover demo controls in both modes. Test fixtures remain isolated from the real-data workflow.

## Data workflow

Follow [REAL_DATA_INPUT_CHECKLIST.md](REAL_DATA_INPUT_CHECKLIST.md), then [REVIEWED_ML_PIPELINE.md](REVIEWED_ML_PIPELINE.md). Keep source files immutable. Do not edit generated hashes, manufacture coverage polygons, lower eligibility thresholds or move synthetic examples into a real dataset.

The reviewed event schema is distinct from the legacy hotspot feature vector. Keep both contracts stable until a separately planned migration. `training_ready=false` is an expected, tested outcome when evidence is missing.

The synthetic `app.ml.train_model` command is retained for compatibility with old demonstrations. It is not part of setup or the real-data training workflow. Learned anomaly experiments and SHAP remain optional and unvalidated; do not run them simply to populate a dashboard.

## Small-team workflow

Pick one feature or defect per change. Include the user-visible behavior, a short reason for the design, and relevant test commands. Record actual source acquisition/review work as it happens. Do not create retrospective commits or invent team contributions or a development timeline.

Keep Python and TypeScript names descriptive. Comments should explain a non-obvious constraint, such as preserving leading-zero acquisition times or excluding future observations. Tiny modules with a real validation boundary are useful; modules that merely forward a single call can be folded into their caller.

## Local artifacts and documentation

Git ignores dependencies, virtual environments, build caches, databases, model artifacts, incoming real data, labels, evidence, generated reports and email files. Schemas, blank templates, the documented tutorial sample, source code and guides stay versioned. Generated demo GeoJSON is recreated by the seed workflow; local copies were preserved when removed from Git tracking.

The README screenshot is deliberately curated documentation and may be versioned. It is a browser capture of tutorial data with an explicit caption, not a generated claim about model performance.

API request and response fields are authoritative in the running `/openapi.json`. The static route inventory in [API.md](API.md) must be updated alongside route changes. Historical phase reports are indexed separately in [docs/README.md](README.md); they are snapshots rather than current promises.

## Stable preparation commands

The existing `python -m app.ml.data.preprocessing`, `python -m app.ml.build_dataset` and `python -m app.ml.readiness` entry points remain. The first now owns normalization; the second owns clustering as well as enrichment. Set `PYTHONPATH=backend` when invoking them from the repository root. Use `--help` to inspect options without processing data.

`routers/context.py` owns the existing infrastructure, zone and satellite-read paths; analytics and history share `routers/analytics.py`. The [MVP refactor report](archive/MVP_REFACTOR.md) records dependency checks and preserved contracts. No compatibility wrappers were added.
