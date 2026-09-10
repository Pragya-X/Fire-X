# Technical debt and next work

There is no schedule or completion percentage here. Each stage depends on evidence from the previous stage. The project currently remains data-blocked.

## Next: obtain a defensible dataset

| Work | Why it matters | Completion evidence |
|---|---|---|
| Acquire representative India FIRMS data | Tutorial and demo observations cannot support an India model | Source manifests, hashes, sensor/season/region coverage and quality reports |
| Supply industrial, land-cover and administrative references | Missing context cannot be filled with seeded geometry | Verified identities, historical validity, CRS/category mappings and surveyed coverage |
| Review event labels independently | Proximity and persistence are not ground truth | Evidence packets, independent reviewers, conflict resolution and agreement analysis |
| Audit groups, histories and splits | Repeated facilities and neighboring events can leak | Reviewed spatial groups, strict earlier history, temporal purge and retained class coverage |

Keep the current gate blocked until these inputs pass its existing checks. Engineering minimum counts are not a statistical sample-size justification.

## Then: evaluate practical models

Compare Logistic Regression, Random Forest and the required optional booster on the reviewed dataset. Select with validation data; evaluate the selected model on held-out data. Check errors by class, region, season and facility, and assess calibration before describing probabilities as calibrated.

Technical gaps include external validation, confidence intervals accounting for event/facility dependence, representative sampling, calibration fitting and reproducible optional dependency locks. Hyperparameter search and additional models need a clear experimental question. Preserve experiments separately from any approved deployed artifact.

The existing learned anomaly and SHAP code is optional tooling, not a validated result. Normal-operation labels are separate from event-source labels. Consider these experiments only after there is independent evidence to fit and evaluate them.

## Before public deployment

| Debt | Current limitation | Required evidence |
|---|---|---|
| Dependency updates | Existing audit records identify frontend dependency issues; this refactor removed an unused package, not the security findings | Supported dependency versions plus backend/browser/build regressions and a fresh audit |
| Legacy API authorization | Several read routes and Q&A remain public | Explicit access policy and authorization tests |
| Session/OAuth hardening | Browser bearer tokens; production Google OAuth is disabled pending review | Threat review, tested session lifecycle, rate limiting and hardened OAuth before enabling it |
| PostGIS migration | SQL exists; SQLite tests do not exercise native geometry/index behavior | Migration, query plans, backup/restore and rollback checks on a real instance |
| Container/TLS deployment | Compose definitions exist; no runtime certification | Clean build, health checks, TLS, storage ownership and deployment smoke tests |
| Event streaming | Process-local queues; no cross-worker fan-out or backpressure policy | Measured load need and a tested multi-worker design if required |
| Provider/storage behavior | Real land cover uses supplied files; unused S3 code has been removed and SMS reports unavailable | Add integrations only for a concrete workflow, with failure, permission and format checks |
| Error contracts | Some legacy handlers return error objects with HTTP 200 or propagate provider errors | Consistent status codes without breaking documented clients |
| Health semantics | Some component entries describe configuration rather than an active dependency probe | Measured checks with clear configured/unavailable/healthy distinctions |
| Scale | Some list/history/export paths scan or return large collections | Representative volume tests, pagination and bounded resource use |
| Lint and accessibility | Typecheck/build run; lint is skipped and UI coverage is narrow | Noninteractive lint setup and keyboard/mobile/accessibility checks |

## Later, only if justified

- Pixel-based satellite evidence using sourced imagery and quality masks.
- Better acquisition-opportunity handling for recurrence and missing observations.
- Consolidating the legacy demo and reviewed-event interfaces through an explicit migration.
- Applying real user preferences if users need them; inactive controls were removed.
- Offline field review or multilingual presentation after the core review workflow is used.

Multimodal models, autonomous reasoning, agent systems, research ensembles and multi-region expansion are outside the present scope. None is needed to make the current dataset pipeline honest or useful.
