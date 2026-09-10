# SIH 26162 — ML/data pipeline, phases 1–6

> Historical snapshot. Use [the documentation index](../README.md) for current guides. Recorded results and phase instructions below describe that earlier check.

Implementation stops at **unlabeled event data**. No real classifier has been
trained or evaluated. The existing rule classifier and synthetic demo generator
remain available. Event features do not silently replace the legacy 14-feature
vector used by the dashboard.

## Run locally

Use Python 3.12 (matching the existing Dockerfile). From the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/python -m app.ml.data.preprocessing \
  --input data/samples/firms_nasa_tutorial.csv \
  --source https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html
PYTHONPATH=backend .venv/bin/python -m app.ml.build_dataset \
  --input data/processed/firms_clean.parquet \
  --output data/ml/thermal_events.parquet \
  --spatial-km 1 --temporal-hours 24 --history-radius-km 1
```

Both commands accept paths; defaults derive from `DATA_DIR`. Preprocessing accepts
CSV or Parquet; the builder accepts the preprocessed Parquet. Source is required.
Raw files are copied unchanged under `data/raw/firms/` with a content-hash prefix.
The small published NASA tutorial excerpt is for pipeline checks only; replace it
with an appropriately sourced India export and historical observations for the MVP.

For reference enrichment, append:

```sh
--references /path/to/reference_layers.geojson \
--reference-source 'OSM export YYYY-MM-DD + land-cover source/version' \
--reference-crs EPSG:4326
```

See [DATASETS.md](../DATASETS.md) for the explicit reference schema. The seeded GIS
layers are never automatically included in the new event dataset.

## Execution and compatibility

Existing online path remains:
`ingest → analyze_hotspot → temporal → legacy vector → classify_vector → risk → ORM/API`.
Mode/version provenance is returned by classification and stored in explanation
JSON, so historical predictions retain their provenance when the active mode
changes. The ML status API, system health and AI Intelligence page expose mode.
Legacy class names and probability fields remain intact.

New offline path:
`CSV/Parquet → validation + rejection report → clean observations → haversine/time
connectivity → event aggregates → supplied GIS context + past-only history → typed
69-column Parquet + membership + manifest + schema`.

## Explicit model modes

| Setting | Actual behavior |
|---|---|
| `ML_MODE=rules` (default) | Rule scores only; ignores all model files. |
| `ML_MODE=demo` | Loads legacy `MODEL_DIR/model.pkl`; explicitly synthetic, uncalibrated. Missing/corrupt/incompatible artifact uses rules with a reason. |
| `ML_MODE=trained` | Requires trusted `classifier.joblib` and `model_metadata.json`, `training_data_type=real`, a version and exact legacy feature-name order. No such artifact is supplied. |
| `ML_FALLBACK_MODE=rules` | Default when a requested real artifact cannot load. |
| `ML_FALLBACK_MODE=demo` | Explicitly permits a valid synthetic demo artifact on real-artifact failure; otherwise rules. Both requested and actual mode are reported. |

Health reports `model_mode` (`RULES`, `DEMO_MODEL`, `TRAINED_MODEL`), requested
mode, actual artifact path (null for rules), model version, training-data type,
evaluation availability/data type and fallback reason. `baseline` remains the
legacy indicator for rule execution; use `model_mode` to distinguish demo from real.
Trusted local joblib files only: pickle/joblib is executable content, not an upload format.
Real metrics are only shown if their data type and model version match metadata.
Existing demo metrics remain explicitly synthetic. No calibration is implemented
in these phases. Probability, persistence and risk are different quantities.
The rule/context factor dictionary retains its old API key but has
`factor_type=heuristic_context`; it is not model attribution. UI labels reflect this.

`train_model.py` is retained and now writes demo provenance. **Do not run it as
real-model training. No training command was executed for this upgrade.** A future
real event model needs an explicit input adapter and schema contract in Phase 17;
these 69 columns are intentionally not fed directly into the old 14-input model.

## Validation and clustering assumptions

- Latitude/longitude must be finite and in WGS84 bounds. Acquisition date/time
  becomes UTC; HHMM/HH:MM supported. VIIRS `bright_ti4` and MODIS `brightness`
  normalize to `brightness` while original fields are retained.
- Missing FRP/brightness/daynight/sensor are nullable; invalid supplied thermal
  values reject a row. FRP must be nonnegative and brightness positive. No
  unvalidated upper temperature cutoff is imposed. Native confidence stays native.
- Duplicate identity is coordinate + UTC time + satellite + instrument. Keep the
  first observation and retain duplicate rows with reasons in the rejection CSV.
  This does not merge distinct sensors or adjacent pixels. Measurements are not
  averaged when duplicates disagree; review the raw/rejected records.
- Each edge requires haversine distance ≤1 km AND time separation ≤24 h by default.
  Connected components are equivalent to DBSCAN with `min_samples=1`. Isolated
  observations remain singletons. Thresholds are adjustable engineering defaults,
  not validated fire-event boundaries. Chaining may merge long-lived sources or
  nearby incidents; inspect event radius/duration and tune per sensor before labeling.
- IDs hash sorted member detection IDs and clustering parameters. Reordering
  clean rows does not change results. Adding observations can change event identity.
- Spherical centroids handle the dateline. Distances are km; thermal statistics
  omit nulls and use population standard deviation (one value → 0).
- Mixed sensors are preserved as sorted sensor sets. Their brightness channels
  are not harmonized; sensor-specific analysis is required before real training.
- BallTree reduces candidate search; dense colocated observations can still cause
  quadratic work. Process bounded regions/date windows for large archives, then
  reconcile clusters across partition boundaries (not implemented yet).

## GIS assumptions

Haversine ranks point candidates; local WGS84 azimuthal-equidistant projection
measures polygon/line distances and 1 km buffer areas. `always_xy=True` fixes axis
order; holes/multipart geometries are retained. Boundary points count as covered.
Typed facility footprints provide footprint distance; point-only facilities provide
point distance. Missing layers → null in event features (legacy APIs retain -1).
Counts describe **observed assets**, not completeness. Polygon overlap false means
no overlap in supplied geometries; it does not prove absence in incomplete OSM.
Area fractions require an explicit layer coverage polygon covering the entire
buffer. Otherwise null. Overlapping polygons are unioned before measuring area.
Very large/antipodal or dateline-crossing reference polygons require upstream
clipping; projected straight edges approximate boundaries. No raster land-cover
provider has been added. Unknown legacy land cover now deterministically returns
`Other` rather than a random category.

## Temporal assumptions

Event history uses observations within the configurable neighborhood and
`[event_start − 90 days, event_start)`. Every current-event detection is excluded.
All features are based on available observations: zero count does not establish
that a sensor observed the site and saw no activity. The manifest records this
policy; retain source acquisition coverage before making scientific claims.

Counts and unique UTC active days use 1/7/30/90-day windows. Previous-detection time
and cadence are hours. Mean/median/std/max FRP, brightness mean, FRP delta/ratio/
z-score are past-only; zero baseline ratio and zero-variance z-score remain null.
Recurrence is active UTC days / 90. Spatial location variance is mean squared
radial distance to the event centroid in km², not lat/lon-degree variance.
Day/night ratios divide by all historical detections; unknowns can make their sum <1.

Event persistence/pattern summarize prior history **plus the current event**, as of event
end; this allows a long current event to demonstrate recurrence without contaminating
its historical FRP baseline. The evidence records current-event active days separately.

Legacy temporal analysis now filters its actual window, excludes future values,
and deduplicates times. Its retained heuristic persistence score uses
`min(100, 6 × active_days + 25 × regularity + 15 × coverage)` for ≥2 unique times,
where regularity is `max(0, 1 − min(1, gap_CV/1.2))` and coverage is capped at 1
from observation count × mean gap / window duration. Singleton score is 0.
Pattern cutoffs (50 points, 36/48 h cadence, 24 h gap variability, 72 h recency)
remain engineering heuristics, not validated scientific thresholds. Event evidence
also exposes historical FRP variability, spatial consistency and industrial
proximity. Multi-signal persistent-source classification remains Phase 18.

## Outputs and inspection gate

- `data/processed/firms_clean.parquet`
- `data/processed/firms_clean.validation.json`
- `data/processed/firms_clean.rejected.csv`
- `data/ml/thermal_events.parquet`
- `data/ml/thermal_events.membership.parquet`
- `data/ml/thermal_events.manifest.json`
- `data/ml/thermal_events.schema.json`

The validator checks identifiers, coordinates, time ordering, finite values,
proportions and membership conservation; the manifest lists null counts, sources,
input/reference hashes and parameters. It always marks `training_ready=false`:
unlabeled event data is not evidence of classification performance. Inspect events,
reference coverage, sensor mixtures and long chains before Phase 7 labeling.

## Checks

```sh
.venv/bin/python -m pytest backend/tests -q
cd frontend
npm ci
npm run typecheck
npm run build
```

Tests that seed demo users should use an isolated test database and `DATA_DIR`.
The recorded acceptance run used `/tmp/sih-phase6-tests` and disabled SMTP, so no
email was sent. Backend test fixtures are synthetic unless explicitly documented
as the NASA excerpt. No real held-out evaluation was conducted.

## Next data-readiness stage (no training)

[INDIA_DATA_READINESS.md](../INDIA_DATA_READINESS.md) documents the new multi-file
preprocessor, `--reference-bundle` and `app.ml.readiness` commands. These reuse the
existing GIS/event/history code and retain the 69-column schema. The training gate
stays false. Per-feature coverage, null-history reasons and a human inspection
sample are now available; absent India inputs produce an explicit blocked report.
