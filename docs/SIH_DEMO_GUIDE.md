# SIH demo and judge walkthrough

Open by stating: “The ingestion, GIS, review and experiment tooling is implemented. The current repository has no representative India dataset or reviewed labels, so real training and evaluation are blocked.” Do not present the five-row NASA tutorial excerpt as India data or a performance benchmark.

## Live product sequence (approximately eight minutes)

1. Open System Health and AI Results. Point out rules mode, no real evaluation and unavailable dependencies/providers where shown.
2. Open Home / Live Map only as a **scripted demonstration**. It uses seeded infrastructure/hotspots and synthetic satellite illustrations. These are not validation data.
3. Open Event Evidence. With no imported real events, show its explicit empty state. For a formatting demonstration, an administrator may import the hash-complete `data/ml/tooling_verification/thermal_events.parquet` produced from the documented NASA excerpt. Explain that its three candidate events are in Africa; do not label them as India incidents.
4. Select an imported event. Show source hashes, observation times, unavailable context/history, null confidence and the Unknown decision. Toggle the event-density heatmap and step the timeline. Export the actual loaded records.
5. Demonstrate a draft **Unknown** annotation. Submit it and have a second analyst review the exact evidence. Unknown remains ineligible for training. Do not invent a known class for presentation convenience.
6. Show the preparation manifest and the readiness report listing blockers. Explain facility/location grouping, temporal embargo, independent labels and held-out testing.
7. Show the requirement/evidence report and discuss the collection/validation plan. Do not show a fabricated accuracy dashboard.

## Five scenario discussion cards

These are walkthrough scripts and evidence requirements, not fabricated detections or ground-truth labels. The existing scripted escalation can illustrate UI behavior for the first two; the remaining cases should use Unknown/insufficient-evidence states until a real, consented, source-documented case is available.

| Scenario | Demonstrate | Evidence required before a real claim | Correct current behavior |
|---|---|---|---|
| Industrial Fire | Sudden thermal deviation, facility context, analyst escalation; existing seeded scenario is explicitly synthetic | Verified incident time/location and independent field/imagery evidence; sufficient normal-operation baseline | Flag review if supported; Unknown when class evidence/model unavailable |
| Persistent Heat Source | Recurrence, active days and FRP stability over a documented history window | Longitudinal coverage plus verified industrial operation; account for missed overpasses/clouds | Persistent candidate is a heuristic, not a confirmed source label |
| Wildfire | Contrast vegetation context with industrial proximity | Independent fire evidence and verified land-cover/temporal match | Forest context alone does not turn an unknown into Wildfire |
| Gas Flare | Explain why constant industrial heat can be expected operation | Verified flare installation/operation, time match and distinguishing evidence | No flare claim from persistence or oil/gas proximity alone |
| Unknown Event | Missing references/history or conflicting evidence, null confidence, rejected/uncertain labeling | More independent evidence before a known class can be assigned | Explicit abstention; excluded from training even if reviewed |

## Questions judges should be able to verify

- Can a high-FRP point automatically become ground truth? No.
- Can reviewers approve their own labels? No; the API rejects it.
- Can stale source files or edited split assignments train a model? The gate checks hashes and rebuilds the dataset before fitting.
- Are reference absence and observed zero interchangeable? No; coverage must be supplied and reviewed.
- Are learned anomaly models deployed? No. Isolation Forest/One-Class SVM are gated offline tooling; the current API uses an explicitly heuristic statistical baseline.
- Are SHAP, calibrated probabilities, accuracy, response latency, nationwide coverage or SIH performance demonstrated? Only claim results that have been generated and verified. Current real-model metrics are unavailable.
- Was PostGIS tested? Its schema/migration is written; native execution remains unverified here.

Judging score cannot be estimated defensibly without the official rubric, real validation results and an observed presentation. The evidence report is an internal checklist; it does not calculate a judging score or win probability.
