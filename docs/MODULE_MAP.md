# Application module map

Inventory for the September 2026 refactor. Each row identifies an existing source module and its top-level responsibilities. This is a navigation aid, not an assertion of production or scientific validation. Removed modules are listed in [PROJECT_REVIEW.md](archive/PROJECT_REVIEW.md).

## Backend

Package `__init__.py` files only establish import boundaries and are retained.

| Module under `backend/app/` | Top-level responsibilities |
|---|---|
| `auth.py` | `hash_password`, `verify_password`, `create_access_token`, `decode_token`, `get_current_user`, `require_role` |
| `config.py` | `Settings` |
| `create_admin.py` | `main` |
| `database.py` | `Base`, `get_db`, `init_db`, `check_db` |
| `event_models.py` | `ThermalEvent`, `EventPrediction`, `EventAnnotation`, `ThermalObservation`, `ReferenceFacility` |
| `gis/engine.py` | `haversine_km`, `validate_coordinates`, `local_transformer`, `Feature`, `GeometryFeature`, `SpatialDataset`, `compute_infrastructure_features`, `wkt_point`, `geojson_points` |
| `main.py` | `lifespan`, `root`, `health`, `request_logging` |
| `ml/anomaly.py` | `main` |
| `ml/build_dataset.py` | `ClusteringConfig`, `spherical_centroid`, `cluster_events`, `build_event_dataset`, `build_files`, `main` |
| `ml/data/preprocessing.py` | `acquisition_datetime`, `normalize_firms`, `load_firms`, `preprocess`, `main` |
| `ml/datasets.py` | `typed_events`, `validate_event_dataset`, `feature_schema` |
| `ml/evaluation.py` | `evaluate` |
| `ml/features.py` | `land_cover_code`, `satellite_score`, `time_of_day_value`, `build_feature_vector`, `explain_factors_from_vector` |
| `ml/import_events.py` | `import_events`, `main` |
| `ml/labels.py` | `Annotation`, `validate_annotations` |
| `ml/normal_reviews.py` | `validate_normal_reviews` |
| `ml/predict.py` | `rule_scores`, `rule_classify`, `load_model`, `model_available`, `model_predict`, `contextual_factors_for`, `classify_vector`, `classification_health` |
| `ml/readiness.py` | `feature_coverage`, `history_diagnostics`, `clustering_audit`, `inspection_sample`, `generate_report`, `main` |
| `ml/reference_audit.py` | `audit`, `main` |
| `ml/reference_bundle.py` | `ReferenceBundleError`, `sha256`, `load_reference_bundle` |
| `ml/spatial_features.py` | `event_spatial_features`, `load_reference_geojson`, `load_reference_document` |
| `ml/splits.py` | `SplitConfig`, `leakage_groups`, `make_splits`, `audit_splits` |
| `ml/train_model.py` | `main` |
| `ml/training.py` | `write_json`, `assess_inputs`, `prepare`, `check_gate`, `train`, `main` |
| `models.py` | `utcnow`, `User`, `Hotspot`, `InfrastructureFeature`, `Infrastructure`, `HistoricalDetection`, `IndustrialZone`, `Alert`, `SatelliteValidation`, `ActivityLog`, `Notification` |
| `providers/firms.py` | `ProviderUnavailable`, `FireDataProvider`, `FirmsProvider`, `DemoFireDataProvider`, `UnavailableFireProvider`, `get_fire_provider` |
| `providers/landcover.py` | `LandCoverProvider`, `SeededLandCoverProvider`, `UnavailableLandCoverProvider`, `get_landcover_provider`, `FileLandCoverProvider` |
| `providers/osm.py` | `OsmProviderUnavailable`, `OsmProvider`, `SeededOsmProvider`, `get_osm_provider`, `load_network_geojson`, `load_landcover_geojson`, `reference_features` |
| `providers/satellite.py` | `SatelliteProvider`, `DemoSatelliteProvider`, `LiveSatelliteProvider`, `UnavailableSatelliteProvider`, `get_satellite_provider` |
| `routers/alerts.py` | `list_alerts`, `update_alert`, `acknowledge`, `escalate`, `resolve`, `list_notifications`, `mark_notifications_read`, `mark_notification_read` |
| `routers/analytics.py` | `analytics`, `historical_records`, `playback_days`, `recurring_hotspots`, `timeline_summary` |
| `routers/auth.py` | `login`, `me`, `google_login`, `google_callback`, `change_password`, `forgot_password`, `reset_password`, `create_user` |
| `routers/context.py` | `list_infrastructure`, `infrastructure_geojson`, `network_geojson`, `landcover_geojson`, `list_zones`, `zones_geojson`, `zone_detail`, `list_validations` |
| `routers/copilot.py` | `copilot_ask`, `suggestions` |
| `routers/events.py` | `list_activity`, `stream` |
| `routers/hotspots.py` | `list_hotspots`, `hotspot_stats`, `hotspots_geojson`, `export_hotspots`, `get_hotspot`, `hotspot_report` |
| `routers/ingest.py` | `get_dataset`, `ingest_firms`, `ingest_demo`, `ingest_osm`, `ingest_landcover`, `refresh_analysis`, `run_classification`, `recalculate_risk`, `validate_satellite` |
| `routers/ml.py` | `classify`, `ml_status` |
| `routers/reports.py` | `incident_report`, `daily_report`, `zone_report` |
| `routers/scenario.py` | `run_scenario`, `scenario_state` |
| `routers/system.py` | `system_health` |
| `routers/thermal_events.py` | `event_or_404`, `serialize`, `serialize_many`, `status`, `list_events`, `export_annotations`, `facility_history`, `detail`, `explanation`, `AnnotationRequest`, `annotate`, `analyze` |
| `schemas.py` | `LoginRequest`, `UserOut`, `LoginResponse`, `ChangePasswordRequest`, `ForgotPasswordRequest`, `ResetPasswordRequest`, `CreateUserRequest`, `HotspotOut`, `HotspotDetailOut`, `IndustrialZoneOut`, `AlertOut`, `AlertUpdate`, `ClassifyRequest`, `ClassificationOut`, `CopilotRequest`, `CopilotResponse`, `ScenarioStep`, `ScenarioRunResponse`, `IngestResult`, `ComponentHealth`, `ExportResponse` |
| `seed.py` | `wipe`, `seed_users`, `seed_zones`, `seed_infrastructure`, `seed_hotspots`, `seed_alerts`, `seed_zones_risk`, `seed_activity_and_notifications`, `write_geojson_files`, `main` |
| `seed_data.py` | `build_agriculture_polygons`, `build_dataset`, `math_cos`, `generate_hotspot_specs` |
| `services/classification_service.py` | `analyze_hotspot`, `refresh_all` |
| `services/copilot.py` | `ask` |
| `services/event_intelligence.py` | `number`, `statistical_anomaly`, `persistence`, `hybrid_decision`, `HistoricalAnomalyModel`, `explain_artifact`, `load_approved_model`, `model_status`, `predict_event` |
| `services/google_auth.py` | `google_configured`, `build_authorize_url`, `fetch_userinfo`, `upsert_google_user` |
| `services/mailer.py` | `send_email`, `send_welcome_email`, `send_password_reset_email`, `send_password_changed_email`, `send_alert_email` |
| `services/notification_service.py` | `NotificationService` |
| `services/report_service.py` | `build_incident_report`, `build_daily_report`, `build_zone_report` |
| `services/risk_engine.py` | `compute_risk` |
| `services/sse.py` | `broadcast`, `event_generator` |
| `services/temporal.py` | `analyze_detections`, `historical_features` |
| `utils/helpers.py` | `risk_level_for`, `clamp`, `Timer` |

## Frontend

Next.js pages/layouts are entry points even when their exported component has no importing module. Shared components remain separate when they own useful UI behavior.

| Module under `frontend/` | Role |
|---|---|
| `app/(app)/ai-intelligence/page.tsx` | Page: (app)/ai-intelligence |
| `app/(app)/alerts/page.tsx` | Page: (app)/alerts |
| `app/(app)/analytics/page.tsx` | Page: (app)/analytics |
| `app/(app)/copilot/page.tsx` | Page: (app)/copilot |
| `app/(app)/event-workspace/page.tsx` | Page: (app)/event-workspace |
| `app/(app)/historical/page.tsx` | Page: (app)/historical |
| `app/(app)/hotspots/[id]/page.tsx` | Page: (app)/hotspots/[id] |
| `app/(app)/hotspots/page.tsx` | Page: (app)/hotspots |
| `app/(app)/industrial-zones/page.tsx` | Page: (app)/industrial-zones |
| `app/(app)/ingestion/page.tsx` | Page: (app)/ingestion |
| `app/(app)/layout.tsx` | Layout and providers |
| `app/(app)/page.tsx` | Page: (app) |
| `app/(app)/profile/page.tsx` | Page: (app)/profile |
| `app/(app)/reports/page.tsx` | Page: (app)/reports |
| `app/(app)/satellite-validation/page.tsx` | Page: (app)/satellite-validation |
| `app/(app)/settings/page.tsx` | Page: (app)/settings |
| `app/(app)/system-health/page.tsx` | Page: (app)/system-health |
| `app/forgot-password/page.tsx` | Page: forgot-password |
| `app/globals.css` | Shared styles |
| `app/layout.tsx` | Layout and providers |
| `app/login/page.tsx` | Page: login |
| `app/reset-password/page.tsx` | Page: reset-password |
| `components/aichat.tsx` | AIChat |
| `components/badges.tsx` | RiskBadge, ClassificationBadge |
| `components/dashboard/hotspot-detail-panel.tsx` | HotspotDetailPanel |
| `components/dashboard/live-feed.tsx` | LiveFeed |
| `components/dashboard/scenario-panel.tsx` | ScenarioPanel |
| `components/data-table.tsx` | DataTable |
| `components/feature-importance.tsx` | FeatureImportance, FactorList |
| `components/gauges.tsx` | RiskGauge, ConfidenceGauge, TrendSparkline |
| `components/layout/app-shell.tsx` | AppShell |
| `components/layout/sidebar.tsx` | Sidebar |
| `components/layout/topbar.tsx` | Topbar |
| `components/map/event-map.tsx` | EventMap |
| `components/map/layer-control.tsx` | LayerControl |
| `components/map/map-legend.tsx` | MapLegend |
| `components/map/map-view.tsx` | DEFAULT_VISIBLE, MapView |
| `components/notification-center.tsx` | NotificationCenter |
| `components/satellite-comparison.tsx` | SatelliteComparison |
| `components/stat-card.tsx` | StatCard |
| `components/system-status.tsx` | SystemStatusBar, SystemStatusPage |
| `components/timeline.tsx` | DetectionTimeline, HistoryTimeline |
| `components/ui/primitives.tsx` | Button, Card, CardHeader, CardTitle, CardBody, Badge, Input, Select, Textarea, Dialog, Skeleton, EmptyState, ErrorState, ToastContext, ToastProvider, useToast, Tabs |
| `lib/api.ts` | API_URL, ApiError, getToken, setToken, login, getMe, changePassword, forgotPassword, resetPassword, getHotspots, getHotspot, getHotspotsGeojson, getHotspotStats, downloadExport, downloadHotspotReport, downloadDailyReport, downloadZoneReport, getInfrastructure, getInfrastructureGeojson, getNetworkGeojson, getLandcoverGeojson, getIndustrialZones, getZone, getZonesGeojson, getAlerts, acknowledgeAlert, escalateAlert, resolveAlert, getNotifications, markNotificationsRead, markNotificationRead, getAnalytics, getHistorical, getPlayback, getRecurring, getTimeline, classifyHotspot, getMlStatus, ingestFirms, ingestDemo, ingestOsm, ingestLandcover, refreshAnalysis, recalculateRisk, validateSatellite, getValidations, runDemoScenario, getScenarioState, askCopilot, getCopilotSuggestions, getSystemHealth, getActivity, streamUrl, getEventStatus, getThermalEvents, getThermalEvent, getEventFacility, exportEventAnnotations, saveEventAnnotation, getEventExplanation |
| `lib/auth.tsx` | AuthProvider, useAuth |
| `lib/search.ts` | searchHotspots |
| `lib/types.ts` | Shared types/configuration |
| `lib/utils.ts` | cn, fmt, fmtDt, timeAgo, download |
| `hooks/useSSE.ts` | useSSE |
| `scripts/start.mjs` | Standalone server startup and static assets |

## Other maintained areas

| Area | Decision |
|---|---|
| `backend/tests`, `frontend/tests/e2e` | Keep existing test groups and add regressions next to related tests. |
| `backend/migrations` | Keep explicit SQL; native PostGIS validation is still outstanding. |
| Dockerfiles and Compose | Keep optional deployment tooling; no new services or deployment claim. |
| `data` schemas, samples and templates | Keep documented provenance and empty examples; ignore actual local inputs and generated outputs. |
| `scripts/build_sih_report.py` | Summarize saved checks with provenance; no grading rubric or hard-coded success claims. |
| `docs` and `REPORT.md` | Current guides are indexed separately from historical audit notes. |
