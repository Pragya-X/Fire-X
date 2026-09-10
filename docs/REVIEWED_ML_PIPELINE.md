# Reviewed event ML pipeline

Current status: training blocked. The only supplied observations are five rows transcribed from NASA's public tutorial, in Africa at one timestamp. They demonstrate formatting and clustering only. No India dataset, reviewed labels, normal-operation outcomes or real reference bundle is present.

## Obtain and validate inputs

From the repository root, activate `.venv` and set `PYTHONPATH=backend`. Commands below are templates for real files; they do not download or invent missing data.

```sh
python -m app.ml.data.preprocessing --input /path/to/india-files/*.csv --source "provider/product/export-date" --region india --output data/processed/firms_india_clean.parquet
python -m app.ml.build_dataset --input data/processed/firms_india_clean.parquet --output data/ml/thermal_events_india.parquet --reference-bundle data/reference_bundle.json
python -m app.ml.reference_audit --events data/ml/thermal_events_india.parquet --bundle data/reference_bundle.json --output reports/ml/reference_coverage.json
python -m app.ml.readiness --events data/ml/thermal_events_india.parquet --clean data/processed/firms_india_clean.parquet --report-prefix reports/ml/india_dataset_validation
```

The existing readiness inspector intentionally exits 2 and remains unreviewed. It is not replaced by a manually edited `training_ready` flag. Import a validated, hash-complete artifact with `python -m app.ml.import_events --events data/ml/thermal_events_india.parquet`; this creates no labels. An older manifest without input/membership/output hashes must be rebuilt with the current builder first.

## Reference schema

Copy `data/reference_bundle.example.json` to the ignored `data/reference_bundle.json`, replacing every placeholder with actual source details. Remove optional transport/water entries if unavailable; their absence must be documented. Industrial, landcover and administrative roles are required by the training gate. Each file requires stable feature IDs, declared CRS, valid geometry, source and version. Use `category_property` and `category_map` for provider classes; explicit null mappings record deliberate exclusions.

Supported roles/categories: industrial (refinery, factory, power_plant, mine, industrial_area, oil_gas, industrial polygons, settlement points), landcover (forest, agriculture, urban, industrial, water), administrative (administrative polygons), transport (road/railway/pipeline lines), water (water polygons). Typed facilities accept points and polygons. Industrial land-cover cells are context, not verified facilities. Top-level `coverage` maps available categories to polygons representing the provider's declared surveyed footprint; mere presence of an asset is not completeness.

## Annotation and independent review

The API/UI uses draft → submitted → approved/rejected revisions. Analysts submit; a different analyst reviews the exact submitted content. Optimistic revision numbers reject stale writes. All revisions remain in the database. Export the latest revisions from `GET /api/v1/thermal-events/annotations/export` to `data/labels/reviewed_annotations.json`. Standalone annotations follow `data/annotation.schema.json`.

Classes are Industrial Fire, Persistent Industrial Source, Wildfire, Agricultural Burning, Gas Flare, Mining, Other and Unknown. This vocabulary is deliberately separate from the legacy demo's six display classes. Do not auto-map predictions into ground truth.

Quality A means direct corroborated evidence; B means strong independent indirect evidence; C means weak/ambiguous evidence. Reviewers must document their evidence basis. Only approved A/B records with annotation confidence ≥0.8 are eligible. Unknown, rejected, submitted and draft records are excluded. Annotation confidence is a review judgment, not model probability.

| Class | Required evidence direction |
|---|---|
| Industrial Fire | Independent incident record/field report or analyzed imagery with documented time/location match; proximity alone is insufficient |
| Persistent Industrial Source | Verified industrial operation and longitudinal evidence; recurrence alone establishes only a candidate |
| Wildfire | Vegetation context plus independently verified fire evidence |
| Agricultural Burning | Crop/field context and independent evidence of agricultural burning |
| Gas Flare | Verified flare installation or operational/imagery evidence distinguishing it from other industrial heat |
| Mining | Verified mine context and evidence attributing the thermal source to mining activity |
| Other | Documented known thermal phenomenon outside the above taxonomy |
| Unknown | Insufficient, conflicting or ambiguous evidence; always abstain from training |

Copy `data/dataset_reviews.example.json` into an ignored local review file. Four qualified reviews are required: representativeness, references, temporal_history and clustering. Each contains `approved`, `reviewer`, an aware ISO `reviewed_at`, exact `event_sha256`, and nonempty `evidence` entries shaped as `{"path":"relative/report.md","sha256":"actual-file-hash"}`. The report must assess seasonality, geography, sensor/time coverage, boundary source, omissions, cluster chaining, facility identity and likely selection bias. A hash binds the reviewed document; it does not prove scientific adequacy or reviewer identity by itself.

## Preparation, splitting and experiments

```sh
python -m app.ml.training prepare --events data/ml/thermal_events_india.parquet --labels data/labels/reviewed_annotations.json --readiness reports/ml/india_dataset_validation.json --reviews data/dataset_reviews.json --output data/ml/training --strategy temporal --train-end 2023-01-01T00:00:00Z --validation-end 2024-01-01T00:00:00Z
python -m app.ml.training train --dataset data/ml/training/training_dataset.parquet --output reports/ml/experiment
```

The dates are examples of syntax, not recommended cutoffs. Select and preregister cutoffs appropriate to the actual collection; the 90-day embargo leaves validation/test starting at least 90 days after their preceding boundary. Groups crossing partitions or embargo regions are removed. The seven known classes require at least 30 eligible events each and five per retained partition. This is an engineering floor, not a statistical sample-size justification.

All split modes group nearby locations and identical facility IDs into connected components. Grouping also expands by each event’s member-radius bounding circle, so chained events cannot hide overlapping footprints behind distant centroids. Geographic/group modes estimate transfer to unseen groups with overlapping calendar periods; **they do not establish future-time performance**. Temporal mode adds ordered cutoffs and history purge. Facility mode requires identity for every event. Splitting may legitimately leave empty or class-incomplete partitions and block training. The radius must span the shared history footprint. Validate footprint overlap and reference identity errors before approval.

Generated outputs: training_dataset.parquet, training_manifest.json, feature_manifest.json, label_quality_report.json and split_report.json. The manifest contains class distribution, missingness, source hashes, version and unranked feature candidates. Coordinates, timestamps, identifiers, provenance and heuristic persistence outputs are excluded from model inputs. Entirely missing columns are removed using the training partition only; imputation/scaling fit only on train.

Training reconstructs the dataset and splits from current sources before fitting. Logistic Regression and HistGradientBoosting are available with base requirements. LightGBM/XGBoost/CatBoost are optional dependencies; absence is reported explicitly. A full comparison remains incomplete until the required boosters run. Selection uses validation macro F1. Only the selected model is assessed on test. Metrics include classification precision/recall/F1, macro/weighted F1, accuracy, confusion matrix, per-class ROC/PR, log loss, Brier scores and populated reliability bins. No metric is produced when training is blocked. External validation, bootstrap intervals, hyperparameter search and calibration fitting remain future work.

## Explanations and deployment

Permutation importance measures changes in validation macro F1. Optional SHAP explains the full fitted preprocessing/model pipeline and keeps raw feature order. Install `backend/requirements-ml-optional.txt` in a dedicated experiment environment and lock exact versions before running. SHAP output is unavailable until a real approved artifact exists; no heuristic is presented as SHAP.

The runner writes `event_classifier.joblib`; it never replaces legacy model files or deploys itself. An operator must place a trusted artifact inside MODEL_DIR, retain the reviewed training inputs, and provide a sibling `event_classifier.approval.json` with `deployment_approved: true`, `reviewer`, `reviewed_at`, `evidence`, exact `artifact_sha256`, and `training_dataset_path`. Set EVENT_MODEL_PATH only after review. The loader rechecks the training gate before deserialization. Joblib is executable serialization: never use uploaded or untrusted artifacts.

`POST /api/v1/thermal-events/{id}/analyze` appends a prediction with the currently approved model or evidence rules. `GET .../{id}/explanation?shap=true` requests an analyst-only current explanation; it does not rewrite stored predictions. Stored decisions can be older than the currently configured model and retain their version.

## Anomaly experiments

`python -m app.ml.anomaly --dataset ... --normal-reviews ... --output ... --kind isolation_forest` (or `one_class_svm`) uses the same gate. Normal-operation reviews are a separate JSON document with `dataset_sha256` and `reviews`; each row requires event_id, normal_operation=true, annotator, independent reviewer, source, evidence and reviewed_at. At least 30 distinct normal-operation IDs from train are required. A persistent/gas-flare class is not automatically a normal-operation label.

Raw anomaly deviations are reported for test events without inventing anomaly accuracy. The learned anomaly artifacts are offline tooling and are not deployed into the hybrid API. The API currently uses the statistical FRP baseline: at least five historical detections, positive standard deviation, and a signed z-score. The threshold 3 and persistence thresholds (30 observed days, coefficient of variation ≤0.5) are unvalidated heuristics.

Primary API references: [scikit-learn time-series split guidance](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), [SHAP permutation explainer](https://shap.readthedocs.io/en/stable/generated/shap.PermutationExplainer.html). The project implements its own facility/geographic components and timestamp purge rather than relying on row-count gaps alone.
