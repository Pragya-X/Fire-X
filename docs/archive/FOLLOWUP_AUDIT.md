# Follow-up repository audit

This report records the inspection before this follow-up changes application files. The repository already contains a substantial earlier refactor and uncommitted work. The earlier results remain in [PROJECT_REVIEW.md](PROJECT_REVIEW.md); they are not fresh validation of this follow-up.

## Scope and findings

The review covered the backend routers, service/provider boundaries, GIS and ML modules, frontend routes and shared components, tests, dependency/configuration files, documentation, deployment definitions and tracked generated artifacts. [API.md](../API.md) inventories each endpoint and [MODULE_MAP.md](../MODULE_MAP.md) maps the source modules.

| Finding before changes | Evidence | Planned action and reason |
|---|---|---|
| Unused storage hierarchy | `providers/storage.py` has no application consumers; its S3 settings are used only there | Delete the unused adapter and settings. Keep the working local `/storage` mount. S3 upload integration remains future work. |
| Notification abstraction exceeds its needs | Four provider classes serve one dispatcher; only `notification_service.notify()` has consumers | Use direct private functions and retain the dispatcher contract, database notifications and email delivery. Keep SMS explicitly unsupported. |
| Demo routes are exposed with demo mode disabled | `main.py` registers the scenario router unconditionally; its guard checks production only; ingestion mixes demo and ordinary routes | Remove four demo operations from the non-demo API/schema. Retain them only in explicit non-production demo mode to preserve the working demonstration and its tests. Hide corresponding UI controls otherwise. |
| Duplicate full refresh | `run_classification` repeats `refresh_analysis` when no hotspot ID is supplied | Reuse the existing handler with explicit arguments; retain both client paths. |
| Redundant GIS statements | Repeated coordinate checks, unused local tree variables and identical context branches | Simplify statements without changing distance calculations, return values or public signatures. Index-assisted queries remain future optimization. |
| Unused backend settings | No consumers of backend `MAP_TILE_URL` or `PERSISTENCE_WINDOW_DAYS` | Remove them; retain the separate working frontend tile setting. |
| Ignore rules incomplete | No general `coverage/` or temporary-file rules | Add narrowly scoped generated-output patterns. Preserve locally stored data and prior staged removals. |
| README omissions | No explicit technology stack, contributor or license sections | Add factual sections. No invented team roster, license grant or development history. |

## Retained architecture

Keep `backend/app/routers`, `services`, `providers`, `gis`, `ml`, the shared models, and Next.js `app`, `components`, `lib`. A mass move into new directories would add import churn without improving this small project. Keep working supporting pages under More tools. The event workspace already contains both the event list and event details; adding another empty page is unnecessary.

Preserve preprocessing, event clustering, feature engineering, readiness, review, dataset building, leakage-safe splitting and evaluation. Keep the legacy dashboard and reviewed-event pipeline distinct because their data and evidence guarantees differ. No model training is part of this work.

## Status boundaries

**Implemented:** the software paths and tests described in the existing module/API documentation, including the evidence review workflow and training gate.

**Partially implemented:** remote imagery provides catalog metadata, not pixel confirmation; deployment definitions exist but are not a verified Docker/PostGIS deployment; SSE is process-local; learned tooling exists but has no representative India evaluation.

**Future work:** representative acquisition, independent labeling, gated training/evaluation, calibrated performance evidence, SMS, S3 integration and public-deployment hardening.

`training_ready=false` remains required: representative India FIRMS observations, industrial reference coverage, land-cover references and reviewed labels are missing. Tutorial and demo material cannot substitute for these inputs.

## Validation plan

Retain every existing test. Add focused checks for mode-dependent API exposure and notification delivery contracts. Run the backend suite, TypeScript check, production build and browser suite. Compare the non-demo OpenAPI contract against the baseline; only the four explicitly isolated demo operations should disappear. Record failures and environmental limits honestly in a separate completion report.
