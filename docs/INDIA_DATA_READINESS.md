# India data readiness — training blocked

This stage extends the verified Phase 1–6 pipeline. It does **not** implement
Phase 7 labels or Phase 8–11 training. At entry the actual artifact manifest had
`training_ready=false`, 3 events and 5 detections; all industrial/land-cover
features and historical FRP baselines were null. No Phase 7 outputs or usable
labels were present. No representative India FIRMS/reference files were found.

## Inputs to supply

1. **India FIRMS observations:** real NASA CSV/Parquet exports in
   `data/input/firms/india/`, including historical observations for your areas
   and sensors. Required columns are latitude, longitude and acquisition_time
   or acq_date + acq_time. FRP, brightness/bright_ti4, satellite, instrument and
   daynight should be preserved along with confidence, scan/track and versions.
   Missing optional thermal values remain null; malformed supplied values are
   rejected with reasons. Keep the source URL/export request, sensor/product
   version, actual coverage dates and any archive selection filters. Earlier
   observations in the 90-day feature window are needed to assess history;
   merely having a long file date range does not establish sensor coverage.
2. **Industrial references:** `data/references/industrial.geojson`, a real
   FeatureCollection with stable feature `id` (or `properties.facility_id`),
   `properties.category`/`facility_type`/`infra_type`, geometry and source tags.
   Supported explicit categories: refinery, factory, power_plant, mine,
   industrial_area, oil_gas, industrial and settlement. Point and facility
   Polygon/MultiPolygon geometries are supported. Generic industrial areas are
   not silently called refineries/factories. Unsupported facility types fail
   validation; do not guess them to satisfy the schema.
3. **Land cover:** `data/references/landcover.geojson`, real polygons with stable
   IDs and forest/agriculture/urban/industrial categories. Supply source/product
   version and CRS. This is a **vector input adapter**, not a raster reader:
   raster products require an externally validated vector export first. No
   polygons or class mappings are inferred from satellite credentials.
4. **Bundle:** copy `data/reference_bundle.example.json` to
   `data/reference_bundle.json`; replace provenance placeholders and specify
   each file's actual CRS. The example has no actual observations or geometry.

EPSG:4326 means longitude/latitude coordinate order. Other pyproj CRS definitions
are supported per layer using `always_xy=True`; geometry is transformed into
WGS84. Reference distances use the existing metric/geodesic GIS routines. Clip
very large reference regions appropriately; this is a bounded regional pipeline,
not a claim of scalable nationwide archive processing in one memory-resident run.

## Deterministic preprocessing

From the repository root, with the existing `.venv`:

```sh
PYTHONPATH=backend .venv/bin/python -m app.ml.data.preprocessing \
  --input data/input/firms/india/*.csv \
  --region india \
  --source 'REPLACE_WITH_REAL_NASA_EXPORT_SOURCE_AND_PRODUCT' \
  --raw-dir data/raw/firms/india \
  --output data/processed/firms_india_clean.parquet
```

`--input` accepts one or more CSV/Parquet paths. Explicit mixed paths or multiple
shell globs are allowed. Supply actual files before running the command. Inputs
are processed in sorted path order; duplicates are detected across files using
coordinate/time/satellite/instrument identity. When measurements conflict, the
first deterministic row is retained and duplicate raw rows remain in the rejection
CSV for review. No input row disappears without a validation reason.

The report records source, sensor set, dates, observed bounds, raw/valid/duplicate
counts, missing-coordinate count, UTC processing timestamp and every input hash.
`input_file` and `input_row` preserve per-file lineage in clean/rejected records.
The `source_row` report field refers to the concatenated input; accompanying
input_file/input_row resolve the original row. Input files are validated separately
before concatenation so a valid file cannot mask another file's missing schema.

`--region india` chooses India output paths and reports rows outside an audit
envelope (67–98° E, 6–38° N). It does **not** filter records, assert sovereign
boundaries or establish representativeness; the envelope includes neighbors.
All input files in a run share the supplied source declaration; record individual
sensor/product versions in original columns and keep distinct provenance runs
where needed. Processing timestamps may differ between runs; clean values and
clustering are deterministic for identical paths/content/configuration.

## Reference bundle

Each layer requires a unique name, role (`industrial`/`landcover`), path, source,
version and input CRS. Paths resolve relative to the bundle JSON. Optional fields:

- `format`: geojson (default) or overpass-json (industrial only).
- `category_property`: source property containing the category, default category.
- `category_map`: explicit source code → canonical category. Map a documented
  out-of-scope category to JSON null to exclude it with an audit record. Unknown
  codes do not default to a known class. Mapping correctness is a human obligation.

Per-feature source tags and geometry are retained. File hashes, source versions,
original CRSs and conversion counts are recorded in the manifest. The combined
`reference_sha256` hashes configuration plus **all layer file hashes**, so changing
geometry changes dataset provenance even when configuration paths stay the same.
Manifest reference_crs is the common internal EPSG:4326; original input CRSs are
recorded in `layers[].input_crs`. Industrial and land-cover sources/versions are
also recorded separately. Repeated/conflicting point facility identities across
layers fail; repeated geometry coverage is unioned for fractions, not double-counted.

An Overpass JSON export can use format overpass-json with EPSG:4326. The converter
reuses the OSM provider module's existing explicit categories: industrial=refinery,
industrial=factory, power=plant, landuse=industrial, man_made=mine. Unknown tags
are reported, not classified as mines. Oil/gas infrastructure must be explicitly
typed in GeoJSON; no unverified oil/gas tag inference is added. Closed way rings
are preserved as polygons; center-only records are marked `center_only` points.
Open ways or relations needing ring assembly must be exported as valid assembled
GeoJSON. Use true geometry when overlap/fraction features matter. This stage does
not make a live Overpass request or claim existing OSM data is complete.

Land-cover industrial polygons contribute industrial *land context*, but are not
counted as facilities and never populate nearest facility ID/type. Known facility
footprints contribute footprint distances; center-only inputs cannot establish
industrial polygon overlap.

## Coverage geometry and unknowns

FeatureCollections may declare `available_categories`, including an explicitly
loaded empty layer, and `coverage` mapping each category to its real valid-data
Polygon/MultiPolygon in the layer's input CRS. Declare coverage only for available
categories; invalid geometry fails. Coverage must come from source acquisition/
survey metadata, not an invented rectangle around observed features.

A feature overlapping the query establishes inside=true. A false inside flag
requires declared coverage at that location; otherwise it is null. Fractions
require coverage of the entire 1 km buffer. Counts are counts of *observed assets*,
not proof of completeness. No facility layer yields null facility counts, even
if industrial land-cover polygons exist. A missing distance is not an assertion
that there is no facility. Non-null distance only measures a known reference
feature; it does not prove that a closer unmapped feature is absent.

## Build and validate

After supplying the real files and configured bundle:

```sh
PYTHONPATH=backend .venv/bin/python -m app.ml.build_dataset \
  --input data/processed/firms_india_clean.parquet \
  --reference-bundle data/reference_bundle.json \
  --output data/ml/thermal_events_india.parquet \
  --spatial-km 1 --temporal-hours 24 --history-radius-km 1

PYTHONPATH=backend .venv/bin/python -m app.ml.readiness \
  --events data/ml/thermal_events_india.parquet \
  --clean data/processed/firms_india_clean.parquet \
  --report-prefix reports/ml/india_dataset_validation \
  --inspection-prefix reports/ml/event_inspection_sample \
  --sample-size 20
```

Existing single-file `--references/--reference-source/--reference-crs` and intentional
no-reference builds remain supported. Do not pass both reference modes. All output
schemas remain thermal-events-v1 (69 columns); diagnostics/provenance are sidecars.
Invalid bundle records write `.reference_validation.json` before failing. No valid
event output is written for a failed build; older existing files are not silently
deleted. Always check command exit status and artifact hashes before using outputs.

The readiness command **intentionally exits 2 (TRAINING BLOCKED)**, even for a
valid unlabeled dataset. It writes useful reports for missing/invalid inputs;
there is no training path. Reports include every feature's non-null/null/count
percentage, industrial/land-cover/temporal summaries, dates, geographic bounds,
source hashes, history reasons and clustering review candidates. Empty datasets
have null percentages, not invented 0% coverage. No target percentages are imposed.

## History diagnostics

History is `[event_start − 90 days, event_start)` within the configured radius;
all current-event observations are excluded from the thermal baseline. Reasons:

| Reason | Meaning |
|---|---|
| NO_PRIOR_OBSERVATIONS | No earlier row anywhere in the supplied observations |
| NO_PRIOR_IN_HISTORY_WINDOW | Earlier rows exist but none within the preceding 90 days |
| NO_MATCH_WITHIN_HISTORY_RADIUS | Earlier rows in the window exist elsewhere, none locally |
| MISSING_HISTORICAL_FRP | Local prior observations lack usable FRP |
| INSUFFICIENT_HISTORY | Fewer than two FRP observations or fewer than two distinct times; a mean may still exist |
| ZERO_HISTORICAL_VARIANCE | FRP baseline exists but z-score denominator is zero |
| CURRENT_FRP_MISSING | Valid variable history exists but no current FRP for deviation |
| AVAILABLE | Variable, multiple-time historical FRP exists |

The report includes actual historical detection IDs and counts. Missing history
never becomes FRP=0. Single-observation std remains the existing population std=0,
with a diagnostic explaining why that is not evidence of long-term stability.
Counts describe detections in the supplied file, not continuous cloud-free coverage.

## Inspection and readiness

The configurable inspection sample is deterministic: it includes missing/present
context and history when available, large radius/duration/count cases, then stable
ID order. It is an inspection sample, not a representative statistical sample.
CSV contains event fields, member observations, historical IDs and PENDING human
review status; Markdown summarizes each event with member records. No labels are
assigned. The assistant can inspect the output, but it is not a substitute for
independent human review of reference accuracy or incident evidence.

Radius beyond the 1 km edge threshold and duration beyond the 24 h edge threshold
are flagged for *chaining review*, not automatically called unreasonable. Nearby
separate event centroids with temporal overlap are inspection candidates, not
proof of over-splitting. Pair reporting is capped at 1,000 and explicitly marks
truncation. No parameters change automatically and no new defaults are recommended
without real evidence. Current tutorial flags do not establish India performance.

Readiness separates DATA_PIPELINE_READY, REFERENCE_COVERAGE_READY,
TEMPORAL_HISTORY_READY, LABELS_READY and TRAINING_READY. Valid nonempty artifacts
can pass the pipeline state. Coverage/history credibility remain NOT_READY until
independent review in a later stage; observed non-null percentages do not establish
scientific readiness. Labels are not supplied or assessed in this stage, and
TRAINING_READY always remains false. This adds diagnostic states without weakening
or replacing the existing training gate.

## Current findings and next work

No real India event file was generated because required real inputs are absent.
`india_dataset_validation.json/.md` report missing artifacts. A separate tutorial
report and inspection sample examine the existing 3 events/5 observations, explicitly
identified as the African NASA tutorial excerpt. Industrial and land-cover context
coverage is 0/3; historical FRP baseline coverage is 0/3. All 3 events have
NO_PRIOR_OBSERVATIONS, no chaining flags and no observed nearby separate-event flags.
These observations cannot establish whether clustering would merge or split real
India incidents correctly. No verified labels, classifier metrics, calibration or
production-integration evidence exists.

Supply the inputs above, regenerate and review the India report/sample, then scope
a separate reviewed-label workflow. Do not proceed to model training yet.
