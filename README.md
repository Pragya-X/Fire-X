<div align="center">

# 🔥 FIRE-X

### AI-Based Detection & Classification of Industrial Fires and Persistent Thermal Sources

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)

**Smart India Hackathon 2026 · PS-26162 · NTRO · Disaster Management**

*NASA FIRMS + OpenStreetMap + Land Cover + Satellite Imagery to detect, classify and monitor fire events across India*

</div>

---

## 📌 Problem Statement

Satellite thermal detections from NASA FIRMS provide location and thermal measurements — but **not confirmed fire causes**. A single detection could be:

- 🏭 An industrial furnace or gas flare
- 🌾 Agricultural burning  
- 🌲 A wildfire
- 🔥 An industrial accident

FIRE-X brings together raw observations, nearby infrastructure data, historical activity, and AI-based classification so analysts can assess the likely source with supporting evidence — and take informed action.

---

## ✨ Features

### 🖥️ Command Center Dashboard
- **Live interactive map** — hotspot markers color-coded by risk level (CRITICAL/HIGH/ELEVATED/MODERATE/LOW)
- **KPI stat cards** — active hotspots, critical events, industrial fires, wildfires, agricultural burns, persistent sources
- **Auto-refresh** every 60 s + manual FIRMS sync button
- **Live event feed** with SSE-powered real-time notifications
- **Hotspot detail panel** — click any map point for instant intelligence

### 🔥 Hotspot Intelligence
- Filterable table with 12+ dimensions (classification, risk, state, district, confidence, date range, proximity to industry/forest/agriculture/settlement)
- **Per-hotspot dossier**: risk gauge, confidence gauge, spatial context (10 infrastructure proximities), 14-day detection timeline, AI explanation with feature importance
- Export in **CSV / JSON / GeoJSON / PDF**
- Per-hotspot incident PDF report generation

### 📊 Analytics
- Recharts visualizations: daily detection trend, classification pie chart, risk bar chart, top industrial zones, recurring hotspots
- 14-day and 30-day trend analysis

### 📅 Incident History (`/historical`)
- **Overview** — 30-day timeline bar chart, KPI cards, classification & risk breakdown
- **Records** — filterable archive table + geographic state-wise breakdown  
- **Recurring** — card grid with risk strips, persistence score bars, location, temporal pattern
- **Map Playback** — animated 14-day map with play/pause/scrub slider

### 🏭 Industrial Zones
- Zone intelligence with nearby hotspot history and incident correlation
- Zone-specific PDF reports

### 🤖 AI Intelligence
- Thermal event evidence review and annotation workflow
- SHAP-based explanations and FRP anomaly detection
- Gemini-powered AI Copilot for natural language queries

### 🛰️ Satellite Validation
- Satellite evidence cross-referencing and validation status tracking

### 🔔 Alerts System
- Configurable risk threshold alerts (default: risk ≥ 80)
- Alert lifecycle: open → acknowledged → escalated → resolved
- Real-time notifications via SSE + SMTP email

### 📋 Reports
- Daily hotspot summary PDF
- Per-hotspot incident PDF
- Zone intelligence PDF

### ⚙️ Data Ingestion
- NASA FIRMS live API sync (auto-scheduled every 15 minutes)
- OSM infrastructure, land cover data ingestion
- Demo data seeding, manual risk recalculation

### 👤 User Management
- JWT auth with role-based access (`admin`, `analyst`, `field`, `viewer`)
- Admin panel for user CRUD, audit activity log

---

## 🏗️ Architecture

```
NASA FIRMS API ──► Ingest & Validate ──► Cluster Events ──► Feature Extraction
                                                                      │
OSM / Land Cover ─────────────────────────────────────────────────────┘
                                                                      │
                                                               SQLite / PostGIS
                                                                      │
                                                               FastAPI Backend
                                                              ╱      │      ╲
                                               Next.js     SSE    Reports  Alerts
                                              Dashboard   Stream    PDF     Email
```

### Component Map

| Layer | Key Files |
|---|---|
| Data Ingestion | `routers/ingest.py`, `services/firms_scheduler.py` |
| GIS Engine | `gis/engine.py`, `ml/spatial_features.py` |
| ML Pipeline | `ml/build_dataset.py`, `ml/training.py` |
| AI Classification | `services/event_intelligence.py`, `services/classification_service.py` |
| Risk Engine | `services/risk_engine.py` |
| Temporal Analysis | `services/temporal.py` |
| Report Service | `services/report_service.py` |
| Notification / SSE | `services/notification_service.py`, `services/sse.py` |
| API Layer | `main.py`, `routers/` |
| Frontend | `frontend/app/`, `frontend/components/` |

---

## 🛠️ Tech Stack

### Backend
| Technology | Use |
|---|---|
| Python 3.12 + FastAPI | REST API, OpenAPI docs |
| SQLAlchemy | ORM (SQLite dev / PostGIS prod) |
| Pydantic v2 | Validation + settings |
| scikit-learn | HistGradientBoostingClassifier |
| pandas / NumPy / PyArrow | Data processing |
| Shapely / PyProj | Geospatial computation |
| ReportLab | PDF generation |
| uvicorn | ASGI server |

### Frontend
| Technology | Use |
|---|---|
| Next.js 14 + React 18 | App Router framework |
| TypeScript 5.6 | Type safety |
| Tailwind CSS 3.4 | Dark-mode UI |
| MapLibre GL 4.7 | Interactive GIS maps |
| Recharts 2.13 | Charts / data viz |
| Google Gemini AI | AI Copilot |

---

## 📁 Project Structure

```
Fire-X/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app, router registration
│   │   ├── config.py                 # All env settings (Pydantic)
│   │   ├── models.py                 # ORM models (hotspots, zones, alerts…)
│   │   ├── gis/engine.py             # Spatial distance calculations
│   │   ├── ml/
│   │   │   ├── training.py           # Gated offline training CLI
│   │   │   ├── build_dataset.py      # Clustering + feature assembly
│   │   │   └── data/preprocessing.py # FIRMS loading, validation
│   │   ├── routers/                  # HTTP route handlers (15 modules)
│   │   └── services/                 # Business logic (12 services)
│   └── tests/                        # pytest test suite
├── frontend/
│   ├── app/(app)/
│   │   ├── page.tsx                  # Dashboard + live map
│   │   ├── hotspots/                 # Detection table + dossier
│   │   ├── historical/               # Incident History (4-tab)
│   │   ├── analytics/                # Charts and trends
│   │   ├── alerts/                   # Alert queue
│   │   ├── industrial-zones/         # Zone intelligence
│   │   ├── event-workspace/          # Evidence annotation
│   │   ├── ai-intelligence/          # AI results
│   │   ├── satellite-validation/     # Satellite evidence
│   │   ├── reports/                  # PDF generation
│   │   ├── ingestion/                # Ingest controls
│   │   ├── system-health/            # Status monitor
│   │   ├── profile/                  # User profile + audit log
│   │   └── admin/                    # Admin panel
│   ├── components/
│   │   ├── layout/                   # AppShell, Sidebar, Topbar
│   │   ├── map/map-view.tsx          # MapLibre GL map
│   │   ├── ui/primitives.tsx         # Design system components
│   │   ├── data-table.tsx            # Sortable paginated table
│   │   ├── gauges.tsx                # SVG risk/confidence gauges
│   │   └── ai-chat-panel.tsx         # Floating AI assistant
│   └── lib/
│       ├── api.ts                    # Typed API client (60+ endpoints)
│       ├── types.ts                  # TypeScript interfaces
│       └── auth.tsx                  # Auth context + JWT
├── ml/models/                        # Approved model artifacts
├── data/                             # FIRMS inbox, archives, ML datasets
├── docs/                             # Architecture, API, deployment guides
├── docker-compose.yml                # Local dev
├── docker-compose.production.yml     # Production (PostGIS)
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+

### 1. Clone
```bash
git clone https://github.com/Pragya-X/Fire-X.git
cd Fire-X
```

### 2. Backend
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
```

### 3. Frontend
```bash
cd frontend
npm ci
cp .env.local.example .env.local
cd ..
```

### 4. Run

**Terminal 1 — Backend:**
```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

- Dashboard → **http://localhost:3000**
- API docs → **http://localhost:8000/docs**

---

## 🐳 Docker

```bash
# Local demo
docker compose up --build

# Production (PostGIS)
docker compose -f docker-compose.production.yml up --build
```

---

## 🔐 Demo Credentials

| Email | Password | Role |
|---|---|---|
| `npgearly@gmail.com` | `admin123` | Admin |

> ⚠️ Demo data is seeded automatically on first startup with `DEMO_MODE=true`. Never use the demo database for real data analysis.

To create a real admin:
```bash
python -m app.create_admin
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./firex.db` | SQLite (dev) or PostgreSQL URL |
| `JWT_SECRET` | *(change me)* | Signing secret (32+ chars in prod) |
| `DEMO_MODE` | `true` | Enable demo data and routes |
| `ENV` | `development` | `development` or `production` |
| `FIRMS_API_KEY` | *(optional)* | NASA FIRMS API key |
| `FIRMS_AUTO_SYNC` | `true` | Background auto-sync |
| `FIRMS_SYNC_INTERVAL` | `900` | Sync interval in seconds |
| `AUTO_ALERT_RISK_THRESHOLD` | `80` | Min risk score for auto-alert |
| `CORS_ORIGINS` | `*` | CORS origins (explicit HTTPS in prod) |
| `ML_MODE` | `rules` | `rules`, `demo`, or `trained` |
| `EVENT_MODEL_PATH` | *(optional)* | Approved model artifact path |
| `SMTP_HOST/USER/PASSWORD` | *(optional)* | Email alert config |
| `OPENAI_API_KEY` | *(optional)* | AI copilot key |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

---

## 📡 API Reference

| Domain | Base Path |
|---|---|
| Auth | `/api/v1/auth` |
| Hotspots | `/api/v1/hotspots` |
| Analytics + Historical | `/api/v1/analytics`, `/api/v1/historical` |
| Alerts + Notifications | `/api/v1/alerts` |
| Industrial Zones | `/api/v1/industrial-zones` |
| Thermal Events | `/api/v1/thermal-events` |
| Ingest | `/api/v1/ingest` |
| Reports | `/api/v1/reports` |
| ML Classify | `/api/v1/ml` |
| System Health | `/api/v1/system-health` |
| SSE Stream | `/api/v1/events/stream` |
| Activity Log | `/api/v1/activity` |
| AI Copilot | `/api/v1/copilot` |

Full docs: **http://localhost:8000/docs**

---

## 🤖 ML Pipeline

```
FIRMS Data → Validate → Cluster Events → Spatial Features
                                               │
                              GIS References (industrial, land-cover)
                                               │
                          Evidence Labels (independent review required)
                                               │
                                    Readiness Gate Check
                                               │
                     Gated Training (HistGradientBoosting + optional XGBoost/LightGBM)
                                               │
                              Evaluation → Operator Approval → Production
```

**Classification features:** brightness, FRP, persistence score, historical frequency, 10 proximity distances, land cover code, satellite score, time of day.

**Current status:** `training_ready=false` — representative India data and reviewed labels are required. Running in `rules` mode until approved model is supplied.

---

## 🧪 Testing

```bash
# Backend
python -m pytest backend/tests -q

# Frontend type check
cd frontend && npm run typecheck

# E2E (Playwright)
cd frontend
npx playwright install chromium
npm run test:e2e
```

---

## 📸 All Dashboard Pages

| Page | URL |
|---|---|
| Dashboard + Live Map | `/` |
| Hotspot Intelligence | `/hotspots` |
| Hotspot Dossier | `/hotspots/[id]` |
| Incident History | `/historical` |
| Analytics | `/analytics` |
| AI Intelligence | `/ai-intelligence` |
| Event Workspace | `/event-workspace` |
| Industrial Zones | `/industrial-zones` |
| Alerts | `/alerts` |
| Satellite Validation | `/satellite-validation` |
| Reports | `/reports` |
| Data Ingestion | `/ingestion` |
| System Health | `/system-health` |
| Profile | `/profile` |
| Admin Panel | `/admin` |

---

## 🗺️ Roadmap

- [x] NASA FIRMS ingestion with automatic scheduling
- [x] Risk scoring and multi-class classification
- [x] Interactive GIS map with real-time markers
- [x] Incident History dashboard with playback
- [x] AI Copilot assistant (Gemini)
- [x] PDF report generation
- [x] SSE real-time notifications
- [x] Evidence annotation workflow
- [ ] Representative India dataset + validated classifier
- [ ] Satellite imagery pixel confirmation
- [ ] Calibrated confidence with geographic transfer
- [ ] Production PostGIS multi-worker validation
- [ ] Mobile field officer interface

---

## 📄 Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | System design and component boundaries |
| [API Reference](docs/API.md) | All endpoints, roles, behavior |
| [Datasets](docs/DATASETS.md) | Data sources and provenance requirements |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Dev setup, test groups, debugging |
| [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Docker, production config, PostGIS |
| [ML Pipeline](docs/REVIEWED_ML_PIPELINE.md) | Training and evaluation process |
| [India Data Readiness](docs/INDIA_DATA_READINESS.md) | Real data requirements |
| [SIH Demo Guide](docs/SIH_DEMO_GUIDE.md) | Hackathon walkthrough |
| [Roadmap](docs/ROADMAP.md) | Technical debt and acceptance criteria |

---

## ⚠️ Important

> This is an **evidence review and dataset preparation prototype**, not a certified emergency-response system. No model trained on representative India data exists yet. Demo data must never be treated as real fire events.

---

<div align="center">

**FIRE-X · National Fire Intelligence Grid · SIH 2026**

*AI · GIS · Real-time · Evidence-based*

</div>
