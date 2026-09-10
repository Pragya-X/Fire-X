"""Summarize saved evidence; never train, assign SIH scores or infer readiness."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

REQUIREMENTS = [('India data pipeline',
  'backend/app/ml/data/preprocessing.py; backend/app/ml/reference_audit.py',
  'test_firms_pipeline.py; test_reference_extensions.py',
  'Real representative India collection and reviewed coverage missing'),
 ('Reference data',
  'backend/app/ml/reference_bundle.py; backend/app/ml/spatial_features.py',
  'test_india_readiness.py; test_reference_extensions.py',
  'Real source versions/coverage missing; raster conversion and relation assembly remain upstream'),
 ('Labeling system',
  'backend/app/ml/labels.py; backend/app/routers/thermal_events.py',
  'test_reviewed_training.py; test_event_workspace.py; browser workflow',
  'Workflow verified; no real labels supplied'),
 ('Training dataset',
  'backend/app/ml/training.py',
  'reports/ml/training_readiness.json',
  'Zero eligible rows; real dataset and label quality still unassessed'),
 ('Leakage-safe splitting',
  'backend/app/ml/splits.py',
  'test_reviewed_training.py',
  'Grouping/purge guards tested; real collection still requires overlap and split review'),
 ('Model training',
  'backend/app/ml/training.py',
  'test_blocked_training_never_fits',
  'Real training blocked; optional boosters not installed/run'),
 ('Model evaluation',
  'backend/app/ml/evaluation.py',
  'test_metric_values_are_computed_and_absent_class_is_unavailable; '
  'test_reliability_bins_cover_extremes_and_edges',
  'Metric arithmetic tested; no project performance, intervals or external benchmark'),
 ('Explainability',
  'backend/app/services/event_intelligence.py',
  'test_event_model_never_loads_unapproved_artifact; explanation API test',
  'No approved model/SHAP library; real attribution path unexecuted'),
 ('Anomaly detection',
  'backend/app/ml/anomaly.py; backend/app/ml/normal_reviews.py; '
  'backend/app/services/event_intelligence.py',
  'statistical anomaly and normal-review tests',
  'Learned anomaly fitting/evaluation/deployment unavailable'),
 ('Persistent source engine',
  'backend/app/services/event_intelligence.py; backend/app/services/temporal.py',
  'test_event_temporal.py; test_anomaly_no_baseline_and_zero_variance_are_unknown',
  'Recurrence/stability heuristics are not validated source identification'),
 ('Hybrid decision engine',
  'backend/app/services/event_intelligence.py',
  'hybrid unit tests and Unknown API/browser tests',
  'Classifier integration tooling exists; no real validation or learned-anomaly deployment'),
 ('GIS database',
  'backend/app/event_models.py; backend/app/ml/import_events.py; '
  'backend/migrations/001_event_postgis.sql',
  'SQLite import/API integration; native SQL inspection',
  'PostGIS server/migration/index execution and scale tests not run'),
 ('Frontend',
  'frontend/app/(app)/event-workspace/page.tsx; frontend/components/map/event-map.tsx',
  'Production build; typecheck; Playwright regression tests',
  'Tiles/live imagery and trained-model panels not empirically validated'),
 ('Deployment and security',
  'docker-compose.production.yml; backend/Dockerfile; frontend/Dockerfile; backend/app/config.py',
  'test_production_configuration.py; auth regression tests; reports/npm_audit.json',
  'Earlier npm audit findings; Docker/PostGIS/TLS/load/operational hardening incomplete'),
 ('Testing',
  'backend/tests; frontend/tests/e2e',
  'reports/backend_tests.xml; reports/backend_coverage.json; reports/frontend_tests.json',
  'Partial coverage; external providers, optional ML, PostGIS and load tests outstanding'),
 ('SIH demo',
  'docs/SIH_DEMO_GUIDE.md',
  'Five explicit scenario walkthroughs and live Unknown review test',
  'Only scripted/Unknown demonstrations; no five real independently verified cases'),
 ('Documentation',
  'docs/ARCHITECTURE.md; docs/REVIEWED_ML_PIPELINE.md; docs/DEPLOYMENT_GUIDE.md; '
  'docs/API_EVENT_REFERENCE.md; docs/DEVELOPER_GUIDE.md; docs/SIH_DEMO_GUIDE.md',
  'Source-linked documentation and reports/openapi.json',
  'Needs deployment-specific runbooks and official SIH rubric mapping'),
 ('SIH evidence check',
  'scripts/build_sih_report.py',
  'reports/sih_readiness.json; docs/SIH_READINESS_REPORT.md',
  'Checklist is internal; no official judging result or certification')]


def read_record(path: Path) -> dict:
    if not path.is_file():
        return {"path": str(path), "status": "not supplied"}
    content = path.read_bytes()
    provenance = {"path": str(path), "sha256": hashlib.sha256(content).hexdigest(),
                  "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}
    if path.suffix == ".xml":
        root = ET.fromstring(content)
        suites = [root] if root.tag == "testsuite" else list(root)
        return {**provenance, "recorded_counts": {
            key: sum(int(s.attrib.get(key, 0)) for s in suites)
            for key in ("tests", "failures", "errors", "skipped")}}
    document = json.loads(content)
    if "stats" in document:
        return {**provenance, "recorded_stats": document["stats"]}
    return {**provenance, "training_ready": document.get("training_ready"),
            "blockers": document.get("blockers", [])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-tests", type=Path, default=ROOT / "reports/refactor/backend-tests.xml")
    parser.add_argument("--browser-tests", type=Path, default=ROOT / "frontend/test-results/results.json")
    parser.add_argument("--readiness", type=Path, default=ROOT / "reports/ml/training_readiness.json")
    args = parser.parse_args()
    records = {name: read_record(path) for name, path in (
        ("backend", args.backend_tests), ("browser", args.browser_tests), ("readiness", args.readiness))}
    report = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Saved engineering evidence; not a new validation run or official SIH assessment",
              "training_ready": records["readiness"].get("training_ready"),
              "production_ready": None, "official_sih_score": None,
              "records": records, "requirements": []}
    lines = ["# Recorded project evidence", "", report["scope"], "",
             "This helper reads local reports without running tests or training. Input hashes and timestamps are recorded in `reports/sih_readiness.json`. Missing evidence remains unavailable. A file's existence does not establish a validated implementation.", "",
             "## Recorded checks", ""]
    for name, record in records.items():
        summary = record.get("recorded_counts", record.get("recorded_stats", {
            "training_ready": record.get("training_ready"), "blockers": record.get("blockers", []),
            "status": record.get("status", "recorded")}))
        lines.append(f"- {name}: `{json.dumps(summary, sort_keys=True)}`")
    lines += ["", "Frontend build/typecheck, native PostGIS, containers, real-model evaluation and security status must be established separately. No grade or readiness percentage is calculated.", "",
              "## Implementation and remaining work", "",
              "| Area | Implementation | Evidence to inspect | Remaining limitation |",
              "|---|---|---|---|"]
    for name, implementation, evidence, limitation in REQUIREMENTS:
        paths = implementation.split("; ")
        missing = [p for p in paths if not (ROOT / p).exists()]
        report["requirements"].append({"area": name, "implementation": paths,
            "evidence": evidence, "limitation": limitation, "missing_paths": missing})
        implementation_text = "; ".join(f"`{p}`" for p in paths)
        if missing:
            limitation += "; missing implementation paths: " + ", ".join(missing)
        lines.append(f"| {name} | {implementation_text} | {evidence} | {limitation} |")
    lines += ["", "Use [the input checklist](REAL_DATA_INPUT_CHECKLIST.md) for missing datasets and [the roadmap](ROADMAP.md) for next steps. Historical evidence does not establish current scientific performance.", ""]
    output = ROOT / "reports/sih_readiness.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "docs/SIH_READINESS_REPORT.md").write_text("\n".join(lines))
    print(f"Wrote {output}; no tests, training or readiness overrides executed.")


if __name__ == "__main__":
    main()
