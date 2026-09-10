# Required real inputs — DATA BLOCKED

No representative India exports, real reference bundle or reviewed labels have been supplied. Training remains blocked. The existing application and readiness checks are unchanged. This delivery adds documentation, empty input folders and templates only; it does not acquire data or train models.

## Supply these datasets

| Input | Accepted delivery to the current loader | Required contents and provenance | Current status |
|---|---|---|---|
| India FIRMS observations and history | Original `.csv`, `.parquet` or `.pq` files; multiple files supported | Actual source/product/version/retrieval time, requested extent, acquisition period, sensor identity, known collection gaps and file hashes | Not supplied |
| Industrial facilities/areas | GeoJSON FeatureCollection; supported Overpass industrial JSON export also accepted | Stable facility/feature IDs; refinery, factory, power_plant, mine, industrial_area, oil_gas or industrial category; true point or polygon geometry; source/version/CRS and omissions | Not supplied |
| Land cover | GeoJSON FeatureCollection of polygons/multipolygons | Categories forest, agriculture, urban, industrial, water as applicable; explicit provider mapping, valid-data coverage, product/version/CRS | Not supplied |
| Administrative boundaries | GeoJSON FeatureCollection of polygons/multipolygons | Stable IDs, administrative names/levels, category administrative, authoritative source/version and boundary coverage limitations | Not supplied |
| Water | GeoJSON FeatureCollection of polygons/multipolygons | Category water, stable IDs, source/version/CRS and known completeness | Not supplied |
| Roads and optional railway/pipeline network | GeoJSON FeatureCollection of LineString/MultiLineString | Categories road, railway, pipeline; stable IDs; source/version/CRS | Not supplied |
| Settlement context | Points in the industrial-reference bundle, or another industrial-role layer | Category settlement, stable IDs, source/version/CRS; explicit completeness limits | Not supplied |
| Reviewed event labels | JSON array matching `data/annotation.schema.json`, ideally exported from the review API | Actual event IDs, known/Unknown class, review state, independent reviewer, annotation confidence, quality, evidence, source, notes and review time | Not supplied |
| Dataset-level review evidence | JSON review object plus local evidence documents | Hash-bound reviews of representativeness, references, temporal history and clustering | Not supplied |

GeoTIFF, Shapefile and GeoPackage are **not direct inputs to the existing reference loader**. If these are the original source format, preserve them and provide a documented, correctly reprojected GeoJSON derivative with stable IDs and category mapping. No conversion or fabricated geometry has been created here. Unsupported/unassembled OSM relations likewise need a correctly assembled source-derived GeoJSON export.

## FIRMS schema and time requirements

Required for ingest: `latitude`, `longitude`, and either `acquisition_time` or both `acq_date` and `acq_time`. Supply time explicitly in UTC: aware ISO timestamps such as the form `YYYY-MM-DDTHH:MM:SSZ`, or provider date plus four-digit HHMM preserving leading zeros. This is format guidance, not a sample observation.

Provide `frp` in MW and `brightness` in kelvin, or the recognized thermal alias `bright_ti4` / `brightness_ti`; preserve original channels such as `bright_ti5`. Provide `satellite`, `instrument`, native sensor-specific `confidence`, `daynight`, and source product/version where available. FRP/brightness are nullable in preprocessing; missingness remains a scientific limitation, not permission to invent values. Confidence categories are retained in their native representation and must not be converted into invented class probabilities.

The validator rejects invalid/out-of-range coordinates, invalid timestamps, negative FRP, nonpositive supplied brightness and duplicate normalized detection identities. It checks source files separately before merging, archives originals with hashes and records rejected rows. Supply original exports without manually changing observations to make them pass.

Representativeness is a review requirement, not a filename or file-count check. Cover the intended India regions, facility types, seasons, sensors and time periods. Supply history for at least the 90 days before events where historical features are to be assessed, and document missing overpasses/time gaps. A future-time benchmark needs enough calendar span for train/validation/test and the existing 90-day purge between windows. More files or detections alone do not prove representativeness.

## CRS, geometry and coverage requirements

- FIRMS latitude/longitude must already be **WGS84 / EPSG:4326 decimal degrees**. Latitude and longitude are separate named columns; do not swap them. The FIRMS loader does not accept arbitrary projected coordinates or reproject them. Range checks alone cannot prove CRS. Record the provider CRS explicitly in delivery metadata.
- For each reference layer, declare its **actual** input CRS in the bundle. Prefer WGS84 GeoJSON with coordinate order `[longitude, latitude]`. The reference loader can transform a declared supported source CRS to EPSG:4326 using `always_xy`; projected exports must preserve x/y order and actual CRS. Never relabel a projected dataset as EPSG:4326.
- Supply nonempty valid geometries: polygons for land cover/industrial areas/administrative/water, points or actual polygons for typed facilities, and lines for transport. Preserve polygon holes and multipart structure. Do not replace unknown footprints with invented circles or boxes.
- Every feature needs a stable `id`, `properties.facility_id`, or `properties.id`. Default category lookup uses `properties.category`; configure `category_property`/`category_map` for other source schemas. Unknown categories and duplicate identities are validation issues.
- A GeoJSON FeatureCollection may declare `available_categories` and a `coverage` mapping from category to the **actual surveyed/valid-data polygon in the input CRS**. Coverage is not the bounding box of the observed features. Do not invent it. Without verified coverage, absence/fractions remain unavailable. Area-fraction features need coverage of the full event buffer.
- Capture source, product version, retrieval date, licensing/usage terms, transformation lineage and known omissions. The runtime bundle requires source/version/CRS/path; the supplied sidecar templates document the additional delivery evidence and are not automatically validated by the loader.

## Reviewed labels and reviews

First generate stable event IDs from actual supplied observations; then review those events. Do not label raw rows with event IDs from the tutorial or derive ground truth from existing classifier predictions, persistence rules or nearest facilities.

Supported labels: Industrial Fire, Persistent Industrial Source, Wildfire, Agricultural Burning, Gas Flare, Mining, Other, Unknown. Each approved record requires annotator, a different reviewer, reviewed_at (timezone-aware, not future), confidence within 0–1, quality A/B/C, source and nonempty evidence references. A means direct corroborated evidence; B strong independent indirect evidence; C weak/ambiguous evidence. Confidence must be supplied by the actual reviewer, not filled from a template.

Only approved A/B labels with confidence ≥0.8 are eligible. Unknown, drafts, submitted/rejected labels and C quality remain excluded. Export one latest revision per event; duplicate/conflicting event IDs must be resolved through review, not majority-voted or silently overwritten. The API retains revision history.

The existing preparation gate requires at least **30 eligible events for each of the seven known classes and five per retained split**. These are engineering floors, not a statistically justified target or guarantee of model quality. Facility/location grouping, event footprints and temporal purge may require substantially more data. Document class balance and missing/uncertain labels before approval.

Dataset reviews cover representativeness, references, temporal_history and clustering. Each real approval must contain reviewer, reviewed_at, exact event_sha256 and evidence entries with a relative document path and the actual file SHA-256. Store evidence under `data/reviews/evidence/`. These checks remain unchanged and unapproved; the templates do not constitute reviews.

## Directory structure

Folders have been created for incoming exports and review evidence. Angle-bracket entries below describe files **you must supply**; they do not exist as fabricated data.

```text
SIH2026/
  data/
    incoming/
      firms/india/
        <original FIRMS export CSV or Parquet files>
      metadata/
        <firms_source_manifest.json>
        <reference provenance sidecars>
    references/
      README.md
      <industrial.geojson>
      <landcover.geojson>
      <administrative.geojson>
      <transport.geojson>
      <water.geojson>
    reference_bundle.json                 # supply populated bundle, not the template
    labels/
      <reviewed_annotations.json>
      evidence/<actual incident/imagery/field evidence>
    reviews/
      evidence/<coverage/history/representativeness review documents>
    dataset_reviews.json                  # actual reviews after real artifacts exist
    templates/
      README.md
      source_manifest.template.json
      reference_bundle.template.json
      reference_layer_metadata.template.json
      reviewed_annotations.template.json  # [] only; no labels
      dataset_reviews.template.json       # all approvals false
    annotation.schema.json                # existing label schema
    raw/firms/india/                       # generated raw archive; do not use as incoming inbox
    processed/firms_india_clean.parquet    # generated only from supplied real files
    ml/thermal_events_india.parquet        # generated event artifacts and sidecar manifests
    ml/training/                          # existing preparation outputs; currently zero eligible rows
  reports/phases_26_35/
    tutorial_validation.json
    india_readiness.json
    india_readiness.md
    data_status.json
```

Copy `data/templates/reference_bundle.template.json` to `data/reference_bundle.json` **before** filling it: paths are relative to the destination in `data/`, not to `data/templates/`. Blank CRS/source/version deliberately fail validation. Preserve original exports, and follow the repository's ignore policy before adding any real data to version control; the new incoming inbox is not automatically protected by the existing raw-data ignore rule.

## Commands for a later, supplied-data run — not executed now

From the repository root, after activating `.venv` and setting `PYTHONPATH=backend`, use actual paths and actual source provenance:

```sh
python -m app.ml.data.preprocessing --input data/incoming/firms/india/*.csv --source "ACTUAL_PROVIDER_PRODUCT_EXPORT_REFERENCE" --region india --raw-dir data/raw/firms/india --output data/processed/firms_india_clean.parquet
python -m app.ml.build_dataset --input data/processed/firms_india_clean.parquet --output data/ml/thermal_events_india.parquet --reference-bundle data/reference_bundle.json
python -m app.ml.reference_audit --events data/ml/thermal_events_india.parquet --bundle data/reference_bundle.json --output reports/ml/reference_coverage.json
python -m app.ml.readiness --events data/ml/thermal_events_india.parquet --clean data/processed/firms_india_clean.parquet --report-prefix reports/ml/india_dataset_validation
```

For Parquet or mixed file types, pass the actual filenames instead of the CSV glob. Replace the uppercase source placeholder with the documented source; it is not a real provider. The current readiness inspector still exits 2 for unreviewed data. Do not edit its result or invoke training to work around it. Reviewed-dataset preparation follows the existing `docs/REVIEWED_ML_PIPELINE.md` only after real inputs and evidence are available.

No training, model selection, integration, SHAP generation or deployment is performed in this delivery. Stop at **DATA BLOCKED** until the inputs above are supplied.
