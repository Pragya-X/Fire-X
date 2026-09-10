# Phase 1–6 implementation audit

> Historical snapshot. Use [the documentation index](../README.md) for current guides. Recorded results and phase instructions below describe that earlier check.

Scope: SIH 2026 problem 26162; stop before labeling/training.

Existing execution: routers/ingest.py → seeded SpatialDataset → analyze_hotspot → analyze_detections → build_feature_vector (14 columns) → classify_vector → compute_risk → Hotspot JSON/WKT storage → FastAPI → Next.js map/detail.

| Component | Decision | Finding / planned change |
|---|---|---|
| FastAPI, ORM, Next.js map | KEEP | Preserve routes, tables and legacy classification names. |
| ml/features.py | KEEP/BUILD | Keep legacy vector; separate nullable event schema prevents silently changing model inputs. |
| ml/predict.py, train_model.py, health | FIX | Explicit rules/demo/trained modes; synthetic artifacts must never masquerade as real. |
| FIRMS provider | FIX/BUILD | CSV time and VIIRS brightness/confidence parsing are incorrect; rows silently discarded. Shared validation and auditable offline preprocessing. |
| GIS engine | FIX/BUILD | Degree-based nearest selection, polygon-hole loss and random unknown land cover; use metric/geodesic queries and explicit missing context. |
| temporal.py | KEEP/FIX/BUILD | Existing cadence interface preserved; enforce window and add past-only thermal/location statistics. |
| Event pipeline | BUILD | No detection clustering, event table dataset, provenance or validation commands exist. |
| OSM/land cover | KEEP/BUILD | Existing Overpass gives centers only; seeded polygons are demonstration data. Explicit imported geometry/source required for real enrichment. |
| Database | KEEP; defer | WKT text is not native PostGIS geometry. Event persistence/migration is phase 23. |
| Satellite provider | Defer; unsafe scientific claims | Live provider generates synthetic indices and claims validation. Do not use these fields in new event dataset. |
| Alerts, auth, Docker | Defer | Full audit beyond this scope. Compose requires PostgreSQL driver absent from requirements; Redis appears unnecessary. |
| Removal | NONE | Preserve demo mechanisms. Remove only inaccurate behavior in touched paths. |

Implementation order: (1) modes and API provenance, (2) validated CSV/Parquet preprocessing, (3) geodesic space/time clusters, (4) nullable spatial enrichment, (5) past-only temporal features, (6) deterministic unlabeled dataset/manifest. Add and run focused tests after each, then backend regression and CLI integration. No model training or invented real data.
