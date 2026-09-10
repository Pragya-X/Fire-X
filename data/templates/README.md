# Input metadata templates — no observations or labels

All templates intentionally contain null/blank metadata, empty arrays, or unapproved reviews. No feature geometry, thermal observation, known-class label, metric or confidence value is provided. They cannot enable training.

- `source_manifest.template.json`: fill from actual FIRMS export provenance. Copy completed documentation to `data/incoming/metadata/firms_source_manifest.json`. This sidecar documents delivery; it is not automatically consumed by the FIRMS CLI.
- `reference_bundle.template.json`: copy to `data/reference_bundle.json` before filling. Layer paths resolve relative to that destination. Supply each actual input CRS, source and version; blank fields deliberately fail validation. No reference geometry is included.
- `reference_layer_metadata.template.json`: one completed provenance sidecar per delivered reference layer, under `data/incoming/metadata/`. It supplements, but does not replace, the bundle/GeoJSON metadata.
- `reviewed_annotations.template.json`: an empty array showing the export container format, not reviewed labels. Follow `data/annotation.schema.json`; only genuinely reviewed records belong in `data/labels/reviewed_annotations.json`.
- `dataset_reviews.template.json`: copy to `data/dataset_reviews.json` only when actual event artifacts and review evidence exist. Leave approvals false until qualified review; do not invent reviewer names, review times, event hashes or evidence hashes.

Full requirements and directory layout: `docs/REAL_DATA_INPUT_CHECKLIST.md` from the repository root. Existing loaders and readiness checks are unchanged.
