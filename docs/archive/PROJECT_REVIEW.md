# Repository review and refactor

This records the earlier refactor. See [the follow-up audit](FOLLOWUP_AUDIT.md) and [fresh results](FOLLOWUP_RESULTS.md) for subsequent demo-route isolation, cleanup and verification.

Reviewed on 8 September 2026. The aim was to make the code and documentation easier for a small student team to maintain while preserving working behavior. No team size, development duration, contribution history or judging result was invented.

The working tree already contained substantial changes from earlier work. This report describes this refactor, not every difference from Git HEAD. Existing data-readiness checks and historical evidence were retained. No training or data acquisition was performed.

## Review scope

The review inventoried backend modules, frontend routes/components/helpers, imports, provider modes, API registration, tests, documentation, dependencies and tracked artifacts. Code changes focus on confirmed duplication, unused code, misleading presentation and a provider fallback defect. This is not a formal security certification or a claim that every future execution path is tested.

See [the module map](../MODULE_MAP.md) for the complete application source inventory. API routes are documented individually in [API.md](../API.md). Test groups are listed in [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md).

## Removed or merged code

| Before | After | Reason |
|---|---|---|
| `backend/app/ml/data/firms_loader.py` | `load_firms` lives in `data/preprocessing.py` | One format-dispatch function, used only by preprocessing; leading-zero handling is unchanged. |
| `backend/app/routers/activity.py` | Activity handler lives beside SSE in `routers/events.py` | Both serve the activity feed; original paths, tags and schemas remain. |
| `frontend/lib/topbar-actions.ts` | Renamed to `frontend/lib/search.ts`; notifications imported directly from `api.ts` | The file's real responsibility is search; forwarding unrelated API imports added no value. |
| Duplicate/unused helpers | Removed `now_utc`, duplicate `haversine_km`, `fmt_dt`, `round1`, `uid`, `isotime` | Repository references use the GIS implementation and existing model/time utilities. |
| Unused UI exports | Removed `StatusDot`, `CheckBadge` and `fmtPct` | No application consumers; retained the badges and formatting helpers actually used. |
| `framer-motion` dependency | Removed from manifest, lockfile and installed dependencies | No imports; no working animation removed. Loading/progress indicators remain. |
| `EsriLandCoverProvider` placeholder | Explicit `UnavailableLandCoverProvider` | No remote raster implementation existed; an imagery key must not advertise land-cover support as live. |
| Inactive settings controls | Account link and refreshable provider status | Theme/map/notification/risk preferences were saved but never read elsewhere. No functioning preference behavior was removed. |

Tiny files that own meaningful boundaries remain: label validation, normal-operation review, event-model approval, evaluation and individual functional page wrappers. Combining those would obscure correctness or create unnecessary coupling. Working optional adapters and experiments remain documented as optional/unvalidated rather than being deleted for appearances.

## Behavior and structure decisions

- Keep one FastAPI application, one Next.js frontend and one database. No service layer or API was added.
- Keep the scientific event workflow separate from legacy demo hotspots and their feature schema.
- Keep the seven requested main navigation entries. Live Map links to the existing home map; Event Details opens the existing imported-event workspace. Other functioning pages remain under More tools.
- Keep route URLs and all 65 OpenAPI operations unchanged. Existing aliases remain for callers even if they are not primary UI actions.
- Reject FIRMS failure with HTTP 503 when demo mode is disabled. The old handler could still insert demo observations after selecting an unavailable provider. A regression test checks that the hotspot count does not change.
- Centralize test environment configuration before application imports. Temporary databases, uploads, model paths and email outboxes prevent tests from altering local working data or using configured delivery credentials. Legacy tests now use that configuration rather than overriding it.
- Keep generated files local. Fifteen tracked generated files were removed from the index: twelve email messages, two demo GeoJSON files and a TypeScript build cache. Their local files remain. Ignore rules cover further generated inputs, labels, models and reports.
- Rewrite README and the project report around the actual problem, workflow and missing inputs. Retain old audit documents with an explicit historical header and an index rather than deleting or rewriting their evidence.
- Replace the report helper's internal score and hard-coded build claims with saved input records, hashes, timestamps and limitations. Missing reports remain unavailable. The helper never asserts readiness based on file existence.

The [architecture document](../ARCHITECTURE.md) explains retained boundaries and the [roadmap](../ROADMAP.md) records technical debt and future work.

## Validation

| Check | Result and scope |
|---|---|
| Existing backend suite after initial cleanup | All original 130 tests passed |
| Backend suite with targeted regressions | 135 passed; two upstream deprecation warnings |
| TypeScript check | Passed |
| Next.js production build | Passed; existing lint skip remains |
| Playwright browser tests | Five passed: original four plus navigation/settings regression |
| API compatibility | Before/after OpenAPI schemas identical, including all 65 application operations |
| Critical ML modules | Eligibility, splitting, readiness, event feature schema, clustering, training gate and evaluation code retained |
| Screenshot | Actual tutorial-based annotation form captured through the browser and visually inspected |

The first browser attempt could not bind a sandboxed port; the next found a missing Chromium binary. After enabling disposable test-server execution and installing the matching browser, all five tests passed. Those environment failures were not silently counted as passes.

Backend coverage was not remeasured in this refactor. Docker, native PostGIS, live providers, public deployment and real model performance were not tested. Backend fixtures and intercepted browser contracts are explicitly test-only. The integration test uses the published NASA tutorial excerpt and saves only an Unknown draft in a disposable database.

Local machine-readable evidence is under `reports/refactor/` and `frontend/test-results/`. These generated outputs are ignored. This checked-in summary records the commands and limitations, not scientific metrics.

## Outstanding work

Representative India observations, industrial and land-cover references, and independent labels remain missing. `training_ready=false` remains correct. The next scientific step is acquisition and review, not training or another model architecture. Public deployment and the broader technical debt listed in [ROADMAP.md](../ROADMAP.md) remain separate work.
