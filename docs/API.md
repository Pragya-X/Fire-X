# API reference

The running FastAPI schema at `/docs`, `/redoc` and `/openapi.json` defines request/response fields and validation. This inventory records every registered application endpoint; request bodies refer to named schemas in those docs. The `/storage` mount serves local files separately.

Use `Authorization: Bearer <access-token>` where required. Roles are ordered viewer → field → analyst → admin. Legacy read routes marked **Public** really are unauthenticated; public deployment needs a deliberate access-policy review.

The main inventory below contains **61 operations** registered with `DEMO_MODE=false`. Explicit non-production demo mode adds the four operations in the demonstration table at the end. Restart after changing mode; the runtime request guard also blocks demonstration requests when mode is disabled.

## Data and behavior

- Hotspot, analytics, report and scenario endpoints use the legacy dashboard store. Data may be seeded; an exported PDF does not make it verified evidence.
- `/thermal-events` reads separately imported event artifacts. See [event review contracts](API_EVENT_REFERENCE.md) for annotation revisions and independent approval.
- `/ml/classify` runs inference, not training. No HTTP endpoint starts model training.
- Missing FIRMS credentials or fetch failure with `DEMO_MODE=false` returns 503 without inserting demo detections. Demo fallback is allowed only in demo mode.
- Satellite catalog lookup supplies metadata; it does not implement image-pixel fire confirmation. Remote land-cover ingestion is unavailable; supply a local reference bundle.
- `/events/stream` is an in-process SSE stream, not a Redis-backed queue.
- `training_ready` in deployed-model status describes the approved artifact; offline preparation remains the authority for a new dataset.

## Errors

Common statuses: 401 authentication; 403 role/review restriction; 404 missing record or disabled demo route; 409 duplicate/stale revision; 422 validation; 503 unavailable FIRMS provider. Some legacy handlers return an error object with 200 or propagate provider exceptions; standardizing them is tracked in [technical debt](ROADMAP.md).

## auth

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | Public | Login | —; JSON: `LoginRequest` |
| GET | `/api/v1/auth/me` | Active user | Me | — |
| GET | `/api/v1/auth/google/login` | Public | Google Login | — |
| GET | `/api/v1/auth/google/callback` | Public | Google Callback | `code`, `state` |
| POST | `/api/v1/auth/change-password` | Active user | Change Password | —; JSON: `ChangePasswordRequest` |
| POST | `/api/v1/auth/forgot-password` | Public | Forgot Password | —; JSON: `ForgotPasswordRequest` |
| POST | `/api/v1/auth/reset-password` | Public | Reset Password | —; JSON: `ResetPasswordRequest` |
| POST | `/api/v1/auth/users` | admin or higher | Create User | —; JSON: `CreateUserRequest` |

## hotspots

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/hotspots` | Public | List Hotspots | `classification`, `risk`, `min_confidence`, `state`, `district`, `status`, `temporal_pattern`, `date_from`, `date_to`, `industrial_proximity`, `forest_proximity`, `agriculture_proximity`, `settlement_proximity`, `search`, `sort`, `order`, `page`, `page_size` |
| GET | `/api/v1/hotspots/stats` | Public | Hotspot Stats | — |
| GET | `/api/v1/hotspots/geojson` | Public | Hotspots Geojson | `classification`, `risk`, `state` |
| GET | `/api/v1/hotspots/export` | Public | Export Hotspots | `format`, `classification`, `risk`, `state` |
| GET | `/api/v1/hotspots/{hotspot_id}` | Public | Get Hotspot | `hotspot_id` |
| GET | `/api/v1/hotspots/{hotspot_id}/report` | Public | Hotspot Report | `hotspot_id` |

## infrastructure

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/infrastructure` | Public | List Infrastructure | `infra_type`, `state` |
| GET | `/api/v1/infrastructure/geojson` | Public | Infrastructure Geojson | `infra_type` |
| GET | `/api/v1/infrastructure/network/geojson` | Public | Network Geojson | — |
| GET | `/api/v1/infrastructure/landcover/geojson` | Public | Landcover Geojson | — |

## industrial-zones

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/industrial-zones` | Public | List Zones | `zone_type` |
| GET | `/api/v1/industrial-zones/geojson` | Public | Zones Geojson | — |
| GET | `/api/v1/industrial-zones/{zone_id}` | Public | Zone Detail | `zone_id` |

## alerts

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/alerts` | Public | List Alerts | `status`, `severity`, `alert_type`, `page`, `page_size` |
| PATCH | `/api/v1/alerts/{alert_id}` | field or higher | Update Alert | `alert_id`; JSON: `AlertUpdate` |
| POST | `/api/v1/alerts/{alert_id}/acknowledge` | field or higher | Acknowledge | `alert_id` |
| POST | `/api/v1/alerts/{alert_id}/escalate` | field or higher | Escalate | `alert_id` |
| POST | `/api/v1/alerts/{alert_id}/resolve` | field or higher | Resolve | `alert_id` |
| GET | `/api/v1/alerts/notifications` | Active user | List Notifications | `limit` |
| POST | `/api/v1/alerts/notifications/mark-read` | Active user | Mark Notifications Read | — |
| POST | `/api/v1/alerts/notifications/{notification_id}/read` | Active user | Mark Notification Read | `notification_id` |

## analytics

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/analytics` | Public | Analytics | — |

## historical

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/historical` | Public | Historical Records | `date_from`, `date_to`, `state`, `classification`, `risk`, `page`, `page_size` |
| GET | `/api/v1/historical/playback` | Public | Playback Days | `days` |
| GET | `/api/v1/historical/recurring` | Public | Recurring Hotspots | — |
| GET | `/api/v1/historical/timeline` | Public | Timeline Summary | `days` |

## ml

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| POST | `/api/v1/ml/classify` | analyst or higher | Classify | —; JSON: `ClassifyRequest` |
| GET | `/api/v1/ml/status` | Public | Ml Status | — |

## ingest

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| POST | `/api/v1/ingest/firms` | analyst or higher | Ingest Firms | — |
| POST | `/api/v1/ingest/osm` | analyst or higher | Ingest Osm | — |
| POST | `/api/v1/ingest/refresh-analysis` | analyst or higher | Refresh Analysis | — |
| POST | `/api/v1/ingest/run-classification` | analyst or higher | Run Classification | —; JSON: `object` |
| POST | `/api/v1/ingest/recalculate-risk` | analyst or higher | Recalculate Risk | — |
| POST | `/api/v1/ingest/satellite/validate` | analyst or higher | Validate Satellite | —; JSON: `object` |

## satellite

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/satellite/validations` | Public | List Validations | `status`, `hotspot_id`, `limit` |

## reports

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/reports/incident/{hotspot_id}` | analyst or higher | Incident Report | `hotspot_id` |
| GET | `/api/v1/reports/daily` | analyst or higher | Daily Report | `days` |
| GET | `/api/v1/reports/zone/{zone_id}` | analyst or higher | Zone Report | `zone_id` |

## system-health

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/system-health` | Public | System Health | — |

## activity

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/activity` | Public | List Activity | `action`, `limit` |

## events

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/events/stream` | Public | Stream | — |

## copilot

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| POST | `/api/v1/copilot/ask` | Public | Copilot Ask | —; JSON: `CopilotRequest` |
| GET | `/api/v1/copilot/suggestions` | Public | Suggestions | — |

## Reviewed thermal events

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/api/v1/thermal-events/status` | Active user | Status | — |
| GET | `/api/v1/thermal-events` | Active user | List Events | `facility_id`, `date_from`, `date_to`, `limit`, `offset` |
| GET | `/api/v1/thermal-events/annotations/export` | Active user | Export Annotations | — |
| GET | `/api/v1/thermal-events/facilities/{facility_id}` | Active user | Facility History | `facility_id` |
| GET | `/api/v1/thermal-events/{event_id}` | Active user | Detail | `event_id` |
| GET | `/api/v1/thermal-events/{event_id}/explanation` | analyst or higher | Explanation | `event_id`, `shap` |
| POST | `/api/v1/thermal-events/{event_id}/annotations` | analyst or higher | Annotate | `event_id`; JSON: `AnnotationRequest` |
| POST | `/api/v1/thermal-events/{event_id}/analyze` | analyst or higher | Analyze | `event_id` |

## Application

| Method | Path | Access | Operation | Parameters / body |
|---|---|---|---|---|
| GET | `/` | Public | Root | — |
| GET | `/api/v1/health` | Public | Health | — |

## Compatibility

Both `/ingest/refresh-analysis` and `/ingest/run-classification` are retained for existing clients. The activity log and SSE handlers share one module but keep their original paths. Interactive documentation assets and `/storage` are not model or dataset ingestion APIs.

## Explicit demonstration mode only

These operations are absent from the real-data API and OpenAPI schema. They are retained for the working local walkthrough and existing tests, not data acquisition or labeling.

| Method | Path | Access | Behavior |
|---|---|---|---|
| POST | `/api/v1/ingest/demo` | analyst or higher | Insert a demonstration detection batch into the legacy store |
| POST | `/api/v1/ingest/landcover` | analyst or higher | Read seeded land-cover polygons and log their count; no real reference installation |
| POST | `/api/v1/scenario/run` | analyst or higher | Run the scripted industrial-fire demonstration; no request body |
| GET | `/api/v1/scenario/state` | Public | Read the last demonstration state |

All four return 404 when `DEMO_MODE=false` or `ENV=production`. Real references are supplied through the documented [file bundle workflow](REVIEWED_ML_PIPELINE.md).
