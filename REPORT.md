# FIRE-X project report

## Problem statement

Satellite thermal detections are useful for finding unusual heat, but they do not identify its cause on their own. A furnace or gas flare can look like a recurring hotspot, while vegetation and crop fires may occur close to industrial sites. A reviewer needs location, history and independent evidence before deciding what happened.

FIRE-X explores this problem for an India-focused Smart India Hackathon project. It is a working review and dataset-preparation prototype. A representative India training dataset has not yet been supplied.

## Objectives
 
- Preserve and validate original FIRMS observations.
- Group related detections into candidate events.
- Add industrial, land-cover and historical context without inventing missing values.
- Support evidence-based labels and independent review.
- Prepare leakage-safe datasets for later model comparison.
- Display observations, explanations and reports in an understandable dashboard.

## Technology stack

Python, FastAPI, SQLAlchemy and SQLite support local development. PostgreSQL/PostGIS configuration and a migration are included for deployment work. Pandas, NumPy, PyArrow, Shapely and pyproj handle data and spatial processing. Scikit-learn provides the core experiment tooling. Next.js, React, TypeScript, MapLibre and Recharts provide the dashboard. Pytest and Playwright cover backend and browser behavior.

## Architecture

The system has one backend, one frontend and one database. Offline Python commands prepare data and run gated experiments. [Architecture](docs/ARCHITECTURE.md) contains the diagram and reasons for the main design choices.

The legacy demo store is kept separate from imported thermal events. This preserves working demonstrations while preventing seeded records from being treated as reviewed training observations.

## Dataset

The repository includes a small published NASA tutorial excerpt for ingestion testing. It is not representative India data. The original demo generator also remains for interface tests, clearly separated from the scientific workflow.

Required inputs are representative India FIRMS exports, industrial facilities and polygons, land cover, administrative references, supporting water/transport context, and independently reviewed event labels. Source versions, CRS, timestamp coverage, licenses and evidence must be documented. See [required inputs](docs/REAL_DATA_INPUT_CHECKLIST.md).

## Methodology

1. Archive source observations and record hashes.
2. Validate coordinates, UTC timestamps, duplicates and thermal fields.
3. Cluster detections using spatial and temporal proximity.
4. Compute spatial context and history strictly before each event.
5. Inspect clustering and evidence; save labels through independent review.
6. Prepare facility/location groups and temporal splits with the existing purge.
7. Run the readiness gate. Missing data or evidence blocks training.
8. Once authorized and ready, compare Logistic Regression, Random Forest and required optional models using validation data. Reserve test data for the selected model.

The evaluation code supports class-wise metrics, confusion matrices and calibration diagnostics. These are implementation capabilities, not results: no real project evaluation has been performed.

## Challenges

The main challenge is obtaining defensible labels, especially for industrial accidents versus routine heat. Other challenges include incomplete facility mapping, mixed pixels, cloud/overpass gaps, event over-merging, seasonal sampling and leakage between repeated observations of the same facility.

The project also has two generations of data models. Keeping their boundary explicit is safer than combining them only to reduce file count. Native PostGIS behavior and real provider performance still need separate validation.

## Testing and validation

The backend tests check API behavior, GIS math, temporal features, ingestion, review rules, leakage guards and blocked training. Browser tests cover unavailable/empty states and a draft review through a disposable FastAPI database. Test fixtures are not scientific datasets.

The [developer guide](docs/DEVELOPER_GUIDE.md) explains how to repeat checks. The [refactor review](docs/archive/PROJECT_REVIEW.md) records the checks actually run for this change. Historical audit notes are retained as dated evidence rather than rewritten as current achievements.

## Limitations

**`training_ready=false`.** Representative India observations, industrial and land-cover references, and reviewed labels are missing. There is no validated classifier, measured India accuracy, calibrated confidence or real-model SHAP result.

The event features describe completed events. Satellite imagery integration currently searches catalog metadata. Some legacy APIs are public, SSE is process-local, and deployment/dependency hardening remains outstanding. The software is not a certified emergency-response system.

## Future work

Acquire and review real data, assess coverage and taxonomy, then run approved model comparisons. After evaluation, investigate calibration, geographic transfer and useful explanations. Image analysis and learned anomaly experiments should follow only if the simpler approach leaves a demonstrated gap. Autonomous agents and multimodal research are not current deliverables.

[Technical debt and roadmap](docs/ROADMAP.md) lists dependencies and acceptance evidence. No team size, elapsed development period, contribution split, SIH grade or commit history is asserted by this report.
