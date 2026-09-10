# Reviewed event API

Interactive schema is served at `/docs`; [API.md](API.md) contains the full route inventory. Use `Authorization: Bearer <access-token>`. Reset tokens cannot be used for API authentication.

| Endpoint | Role | Behavior |
|---|---|---|
| GET /api/v1/thermal-events/status | Any active user | Imported count, deployed event-model state, readiness of deployed artifact and class vocabulary |
| GET /api/v1/thermal-events | Any active user | Date/facility filters, limit 1–1000, offset, total and evidence records |
| GET /api/v1/thermal-events/{event_id} | Any active user | Features, source hashes, latest stored intelligence, up to 1000 member observations and annotation history |
| GET /api/v1/thermal-events/facilities/{facility_id} | Any active user | Reference metadata and up to 1000 associated events; nearest-reference association is not causation |
| POST /api/v1/thermal-events/{event_id}/annotations | Analyst/admin | Append draft, submit, approve or reject with expected_revision |
| GET /api/v1/thermal-events/annotations/export | Any active user | Latest annotation payload per event as a training-preparation JSON array |
| GET /api/v1/thermal-events/{event_id}/explanation?shap=true | Analyst/admin | Current model explanation or explicit unavailable reason; no stored prediction mutation |
| POST /api/v1/thermal-events/{event_id}/analyze | Analyst/admin | Append a prediction under the currently approved event model or evidence rules |
| POST /api/v1/ml/classify | Analyst/admin | Existing legacy hotspot classification, with explicit model provenance |

List filters: `facility_id`, aware ISO `date_from`, `date_to`, `limit`, `offset`. The UI exports the loaded page with its total and filter metadata; this is not an unbounded all-event export. Annotation export currently exports all latest revisions; plan paging for large annotation corpora.

An annotation write carries `expected_revision`, `action` (save/submit/approve/reject), label, confidence (null or 0–1), quality (A/B/C), source, evidence (array of references) and notes. The server supplies actor identity and review time. Review actions approve/reject the exact preceding submitted payload; edited review-form content is not silently substituted. Change the content by saving and submitting a new revision. The original annotator cannot review their submission.

Responses: 401 missing/invalid token; 403 insufficient role/self-review; 404 unknown event/facility; 409 stale/concurrent revision or invalid transition; 422 invalid annotation fields. Import is intentionally a local administrative CLI, not an endpoint that accepts arbitrary filesystem paths or model files.

The event API does not mix legacy demo hotspots with real event records. Stored confidence is null without a trained classifier. FRP z-score, recurrence and heuristic priorities must not be described as calibrated probabilities or measured performance. With a trained model, confidence is explicitly an uncalibrated class probability until calibration evidence supports a stronger claim.
