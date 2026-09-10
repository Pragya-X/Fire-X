# Follow-up refactor results

The [pre-change audit](FOLLOWUP_AUDIT.md) recorded the findings before edits. This follow-up builds on the earlier refactor; it does not rewrite the platform or imply a different team history.

## Changes and reasons

| Change | Reason and resulting behavior |
|---|---|
| Removed `backend/app/providers/storage.py` | No application code used this adapter. Removed its four S3 settings. Local static-file serving remains available. |
| Removed notification provider classes | Replaced the base, in-app, email and SMS classes with two private functions and the existing dispatcher. Database/SSE notifications and email retain their contracts; SMS still reports unavailable. |
| Isolated four demo operations | Demo batch, seeded land-cover preview and scenario operations are absent from the non-demo API/schema. Explicit local demo mode preserves the working walkthrough and tests. Runtime rejection returns 404 with common security headers. |
| Hid demo controls outside demo mode | Home and Ingestion read backend source status. Unavailable status hides the controls. Ingestion copy now describes the reference bundle workflow and conditional fallback accurately. |
| Shared full refresh implementation | Bulk classification calls the existing refresh handler with explicit arguments. Both established URLs and their response contracts remain. |
| Simplified GIS statements | Removed duplicate validation statements, unused local variables and identical branches. Distance calculations, signatures, reference handling and feature outputs remain unchanged. |
| Removed unused settings | Backend `MAP_TILE_URL` and `PERSISTENCE_WINDOW_DAYS` had no consumers. The frontend tile configuration remains supported. |
| Completed ignore rules | Added coverage and temporary-file patterns. No generated-path candidates remained in the Git index check. Existing staged generated-file removals and local data were preserved. |
| Updated documentation | README now includes technology, contributor and license status. API documentation covers all 61 normal operations plus four explicit demo operations. Module inventory, architecture decisions, test groups and roadmap reflect the cleanup. |

Only one additional source file was deleted in this follow-up: the unused storage adapter. No ML module, frontend page or existing test was deleted. The earlier merged/removed files are listed in [PROJECT_REVIEW.md](PROJECT_REVIEW.md).

## Structure and architecture

The final directory tree is in [README](../../README.md#repository-structure); the [architecture diagram](../ARCHITECTURE.md) and decision table describe the boundaries. The existing router/service/provider/GIS/ML layout is retained because moving working files would add import churn without a clearer responsibility split. Working supporting pages remain under More tools. Event listing and details share the event workspace.

Preserving explicit demo mode resolves the request to remove demo APIs while retaining working features. Those operations are removed from the real-data application interface and cannot be used to satisfy readiness.

## Verification

| Check | Observed result |
|---|---|
| `python -m pytest backend/tests -q` | **140 passed**, including all prior tests and five new checks; two upstream deprecation warnings |
| `npm run typecheck` | Passed |
| `npm run build` | Passed; 21 static pages generated; existing lint skip remains |
| `npm run test:e2e` | **7 passed**: all prior browser checks plus demo controls in both modes |
| OpenAPI comparison | Exactly four demo paths removed from non-demo registration; all 61 retained operation contracts unchanged |
| Fresh-process mode tests | 61 normal operations; explicit demo mode adds the four retained demonstration paths |
| ML source hash comparison | All files under `backend/app/ml/` unchanged from the pre-edit baseline |
| Git whitespace check | Passed |
| Generated-file index scan | No dependency, cache, database, model or email artifacts matched the checked patterns |

Local evidence is stored under `reports/followup-refactor/`, with browser results also in `frontend/test-results/results.json`. Those generated records are ignored. The browser suite runs disposable local servers; intercepted fixtures and the published tutorial excerpt are software-test inputs, not scientific evidence. Notification tests intercept email delivery.

No new coverage percentage was measured. No live provider, Docker runtime, native PostGIS deployment, security certification or real model performance was verified. The [roadmap](../ROADMAP.md) retains these limitations and the required follow-up evidence.

## Scientific readiness

**DATA BLOCKED — `training_ready=false`.** Representative India FIRMS observations, industrial and land-cover reference coverage, and independently reviewed labels remain missing. The saved readiness report also records unresolved clustering, history, representativeness and split review. No readiness setting or threshold was changed, no real dataset or label was fabricated, and no model training was run.

The next scientific work is acquiring and reviewing the inputs in [REAL_DATA_INPUT_CHECKLIST.md](../REAL_DATA_INPUT_CHECKLIST.md). Implemented software, optional tooling and future empirical validation remain distinguished in the README and architecture documentation.
