# FIRE-X — Project Report

**Smart India Hackathon 2026 · PS-26162 · NTRO · Disaster Management**
**Prepared:** September 2026

---

## Problem Statement

Satellite thermal detections from NASA FIRMS provide location and thermal measurements — but not a confirmed cause. A single detection could be an industrial furnace, a gas flare, agricultural burning, a wildfire, or an industrial accident. These sources require different responses, but a raw detection alone cannot distinguish them.

FIRE-X addresses this gap for India-focused fire monitoring. It ingests raw FIRMS data, enriches it with industrial infrastructure, land-cover, and historical context, applies AI-based classification with explainability, and presents the evidence to analysts through a real-time command center dashboard. The platform also supports evidence-based annotation and leakage-safe dataset preparation for future model training.

---

## Objectives

1. Ingest and validate original NASA FIRMS observations, preserving source provenance.
2. Group related detections into candidate events using spatial and temporal proximity.
3. Enrich events with industrial infrastructure, land-cover, and historical context.
4. Classify thermal sources using rule-based heuristics and, when data permits, trained ML models.
5. Score and prioritize events by risk level to direct analyst attention.
6. Deliver real-time intelligence via an interactive GIS dashboard with live map, charts, and notifications.
7. Support evidence-based annotation, independent label review, and leakage-safe training data preparation.
8. Produce structured reports (PDF) for incident documentation and zone monitoring.

---

## Technology Stack

### Backend
| Component | Technology |
|---|---|
| API Framework | Python 3.12 + FastAPI |
| Database | SQLAlchemy ORM · SQLite (dev) · PostgreSQL + PostGIS (production) |
| Data Processing | pandas, NumPy, PyArrow, Shapely, pyproj |
| Machine Learning | scikit-learn (HistGradientBoostingClassifier), optional XGBoost/LightGBM |
| Explainability | SHAP (optional), rule-based factor extraction |
| PDF Reports | ReportLab |
| Background Tasks | APScheduler (FIRMS auto-sync every 15 minutes) |
| Real-time | Server-Sent Events (SSE) |
| Email Alerts | SMTP (Gmail app password compatible) |
| Auth | JWT (HS256), Google OAuth (optional), bcrypt hashing |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 14 + React 18 + TypeScript 5.6 |
| Styling | Tailwind CSS 3.4 (dark theme, glassmorphism) |
| Maps | MapLibre GL 4.7 (interactive GIS, clustered markers) |
| Charts | Recharts 2.13 (area, bar, pie, line charts) |
| AI Copilot | Google Gemini AI (@google/generative-ai) |
| Testing | Playwright 1.63 (E2E), TypeScript type checking |

---

## System Architecture

The system comprises a single FastAPI backend, a Next.js frontend, and one database (SQLite locally, PostGIS in production). A background scheduler handles automatic FIRMS data synchronization. An SSE endpoint pushes live events to connected dashboards.

```
NASA FIRMS API ──► Ingest & Validate ──► Feature Extraction ──► DB (SQLite / PostGIS)
OSM / Overpass ──►                              │                         │
Land Cover     ──►                     Risk & Classification          FastAPI API
                                               │                     ╱    │    ╲
                                        Alert Engine           Map    Reports  SSE
                                               │             (Next.js Dashboard)
                                        Email / Notify
```

The demo data store is kept strictly separate from imported thermal events and reviewed annotations, preventing seeded records from contaminating the scientific workflow.

---

## Implemented Features

### Command Center Dashboard
- Live interactive map (MapLibre GL) with hotspot markers color-coded by risk level (CRITICAL, HIGH, ELEVATED, MODERATE, LOW)
- KPI stat cards: active hotspots, critical events, industrial fires, wildfires, agricultural burns, persistent heat sources
- Dashboard auto-refreshes every 60 seconds; manual FIRMS sync available
- Live event feed powered by SSE with instant toast notifications on new alerts
- Clickable map hotspot detail panel with classification, risk, location, and detection time

### Hotspot Intelligence (`/hotspots`)
- Filterable, sortable, paginated detection table with 12+ filter dimensions:
  classification, risk level, confidence, state, district, date range, and proximity to industrial/forest/agricultural/settlement areas
- Full per-hotspot dossier page (`/hotspots/[id]`) with:
  - Risk gauge (SVG) and confidence gauge
  - Detection stat bar (satellite, brightness, FRP, persistence score, temporal pattern, land cover, status)
  - Spatial context table: distances to 10 infrastructure types (refinery, factory, power plant, mine, forest, agricultural area, settlement, road, railway, pipeline)
  - 14-day detection timeline visualization
  - AI explanation panel: model-derived factors, feature importance bars, contextual rule-based factors, reasoning narrative
- Export in CSV, JSON, GeoJSON, and PDF formats
- Per-hotspot incident PDF report generation

### Incident History (`/historical`) — *Rebuilt*
Previously a basic filtered table with a simple playback view. Now a four-tab intelligence dashboard:

| Tab | Contents |
|---|---|
| **Overview** | KPI cards (30-day total, daily average, peak day, recurring count) · 30-day animated bar chart timeline · classification breakdown · risk level breakdown · recent critical incidents list |
| **Records** | Fully filtered historical table (date, state, classification, risk) · geographic state-wise breakdown bar chart |
| **Recurring** | Card grid of all recurring/persistent hotspots with risk-colored side strips, persistence score bars, location, temporal pattern badges |
| **Map Playback** | Animated 14-day map with play/pause/scrub slider · per-day detection stat cards · recurring hotspot panel |

### Analytics (`/analytics`)
- Recharts-powered charts: daily detection trend (area), classification distribution (pie), risk breakdown (bar), top industrial zones, top recurring hotspots, alert status
- Summary KPI row: avg classification confidence, avg risk score, open alerts, top zone risk level

### Industrial Zones (`/industrial-zones`)
- Zone list with nearby hotspot counts and risk level indicators
- Per-zone intelligence detail with historical detection counts, proximity hotspots, and zone-specific PDF reports

### AI Intelligence & Event Workspace
- Thermal event review and annotation workflow for scientific label preparation
- Evidence-based decision engine: returns `Unknown` without sufficient evidence
- SHAP-based explanations (when model and data are available)
- FRP anomaly detection and persistence scoring (descriptive heuristics)
- Gemini-powered AI Copilot for natural language queries about fire events and data

### Satellite Validation (`/satellite-validation`)
- Satellite evidence cross-referencing per hotspot
- Validation status tracking (catalog metadata; pixel confirmation is future work)

### Alerts System (`/alerts`)
- Auto-generated alerts when risk score exceeds configurable threshold (default: ≥ 80)
- Full alert lifecycle: open → acknowledged → escalated → resolved
- SSE-powered real-time notification delivery
- SMTP email dispatch for critical events
- Notification center in topbar with unread badge count

### Reports (`/reports`)
- Daily hotspot summary PDF
- Per-hotspot incident PDF reports
- Zone intelligence PDF reports
- All generated using ReportLab with live data

### Data Ingestion (`/ingestion`)
- NASA FIRMS live API ingestion (manual trigger + auto-scheduled every 15 minutes via APScheduler)
- OSM infrastructure data ingestion via Overpass API
- Land cover data ingestion
- Demo scenario runner for interface demonstrations
- Manual refresh analysis and risk recalculation
- Activity log showing all ingestion events

### User Management & Auth
- JWT-based authentication (HS256, 12-hour sessions)
- Role system: `admin`, `analyst`, `field`, `viewer`
- Admin panel (`/admin`) for full user CRUD
- Password change, forgot password, reset password email flows
- Google OAuth integration (optional)
- Audit activity log per user

### System Health (`/system-health`)
- Live service status: database, FIRMS scheduler, ML model, demo mode
- API version and uptime indicators

---

## Methodology

1. **Archive & validate** — Source FIRMS CSV/Parquet observations are hashed, timestamped, and preserved in `data/raw/`. Coordinate, UTC timestamp, duplicate, and thermal field validation runs before any processing.
2. **Cluster events** — Spatial and temporal proximity clustering groups detections into candidate events. Long chains may form; these remain candidates, not confirmed events.
3. **Feature extraction** — Per-event spatial features are computed from industrial, land-cover, and administrative references. Historical features use observations strictly before event start to prevent leakage.
4. **Classification** — The system runs in rules-based mode (`ML_MODE=rules`) by default, returning evidence-based assessments. A trained `HistGradientBoostingClassifier` is used when an operator-approved model artifact is provided.
5. **Risk scoring** — A deterministic risk engine computes a 0–100 score from thermal intensity, classification confidence, proximity to sensitive infrastructure, and persistence.
6. **Alert generation** — Hotspots exceeding the risk threshold automatically generate alerts and dispatch SSE/email notifications.
7. **Label review** — Independent annotators assess evidence in the Event Workspace and record labels with quality grades (A/B/C), confidence, and source references.
8. **Gated training** — A readiness gate checks dataset completeness, SHA-256 integrity, leakage guards, and review coverage before allowing offline training. Missing data or evidence blocks training (`training_ready=false`).

---

## Dashboard Pages

| Page | URL | Description |
|---|---|---|
| Command Center | `/` | Live map, KPIs, event feed |
| Hotspot Intelligence | `/hotspots` | Filtered detection table |
| Hotspot Dossier | `/hotspots/[id]` | Full per-hotspot analysis |
| Incident History | `/historical` | 30-day archive, recurring analysis, playback |
| Analytics | `/analytics` | Charts and trend analysis |
| AI Intelligence | `/ai-intelligence` | Thermal event classification results |
| Event Workspace | `/event-workspace` | Evidence annotation workflow |
| Industrial Zones | `/industrial-zones` | Zone proximity and risk |
| Alerts | `/alerts` | Alert queue management |
| Satellite Validation | `/satellite-validation` | Satellite evidence records |
| Reports | `/reports` | PDF report generation |
| Data Ingestion | `/ingestion` | Ingest controls + activity log |
| System Health | `/system-health` | Service status monitor |
| Profile | `/profile` | User settings + audit log |
| Admin Panel | `/admin` | User management (admin only) |

---

## Testing and Validation

**Backend (pytest):** API behavior, GIS distance calculations, temporal feature extraction, ingestion pipelines, review rules, leakage guards, activity logging, and blocked-training enforcement.

**Frontend (Playwright):** End-to-end browser tests for auth flows, unavailable/empty states, draft annotation, and dashboard loading. TypeScript type checking runs across all 60+ API calls and component props.

Test fixtures use isolated SQLite databases, mocked SMTP outboxes, and separate upload/model paths. Browser tests run on isolated ports (3101/8101).

---

## Challenges

- **Label quality** — Obtaining defensible labels for industrial accidents vs. routine heat is the primary bottleneck. Proximity and recurrence alone are not valid labels.
- **Reference coverage** — Incomplete facility mapping means some detections lack industrial context, leading to conservative `Unknown` decisions.
- **Mixed pixels and cloud gaps** — Satellite overpass frequency and cloud cover create temporal gaps; persistence patterns can be disrupted.
- **Two data model generations** — Legacy demo hotspots and reviewed thermal events coexist. Maintaining an explicit boundary is safer than merging them.
- **Scalability** — SSE is currently process-local; PostGIS multi-worker production operation requires separate validation.

---

## Limitations

- **`training_ready=false`** — No model trained on representative India FIRMS data exists. The platform runs in rules-based mode.
- No validated India accuracy figures, calibrated confidence scores, or real-model SHAP results.
- Satellite imagery pixel confirmation is catalog metadata only; automated pixel analysis is future work.
- Google OAuth, multi-worker deployment, and load/recovery behavior require additional hardening before production use.
- This is a **prototype for evidence review and dataset preparation**, not a certified emergency-response system.

---

## Future Work

- Acquire and label representative India FIRMS observations with independent review
- Run approved model comparisons (Logistic Regression baseline → HistGradientBoosting → optional boosters)
- Implement calibrated confidence scoring and geographic transfer evaluation
- Integrate satellite imagery pixel-level confirmation
- Validate PostGIS multi-worker production deployment
- Mobile-optimized interface for field officers
- Distributed ingestion queue for high-volume national-scale deployment

---

*[Architecture](docs/ARCHITECTURE.md) · [API Reference](docs/API.md) · [ML Pipeline](docs/REVIEWED_ML_PIPELINE.md) · [Roadmap](docs/ROADMAP.md)*
