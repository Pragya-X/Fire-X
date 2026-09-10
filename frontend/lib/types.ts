export type RiskLevel = "LOW" | "MODERATE" | "ELEVATED" | "HIGH" | "CRITICAL";

export type Classification =
  | "Industrial Fire"
  | "Persistent Industrial Heat Source"
  | "Gas Flare"
  | "Wildfire"
  | "Agricultural Burning"
  | "Other Thermal Anomaly";

export interface User {
  id: number;
  email: string;
  name: string;
  role: "admin" | "analyst" | "field" | "viewer";
  created_at?: string | null;
}

export interface ActivityItem {
  id: number;
  user: string;
  action: string;
  entity: string;
  entity_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface InfrastructureFeatures {
  nearest_refinery_distance: number;
  nearest_factory_distance: number;
  nearest_powerplant_distance: number;
  nearest_mine_distance: number;
  nearest_forest_distance: number;
  nearest_agriculture_distance: number;
  nearest_settlement_distance: number;
  nearest_road_distance: number;
  nearest_railway_distance: number;
  nearest_pipeline_distance: number;
  nearest_refinery_id?: string;
  nearest_settlement_id?: string;
  [key: string]: number | string | undefined;
}

export interface Hotspot {
  id: number;
  code: string;
  external_id?: string | null;
  latitude: number;
  longitude: number;
  acquisition_time?: string | null;
  brightness: number;
  frp: number;
  confidence: number;
  source: string;
  satellite: string;
  classification: Classification | string;
  classification_confidence: number;
  probabilities?: Record<string, number>;
  risk_score: number;
  risk_level: RiskLevel | string;
  persistence_score: number;
  temporal_pattern: string;
  status: string;
  state: string;
  district: string;
  land_cover: string;
  explanation?: Explanation;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface HotspotDetail extends Hotspot {
  features?: InfrastructureFeatures | null;
  history: HistoricalDetection[];
  validations: SatelliteValidation[];
  feature_vector?: number[];
}

export interface PlaybackFrame {
  date: string;
  label: string;
  count: number;
  hotspots: {
    code: string;
    latitude: number;
    longitude: number;
    classification: string;
    risk_level: string;
    risk_score: number;
    brightness: number;
    frp: number;
  }[];
}

export interface HistoricalDetection {
  id: number;
  detection_time: string;
  brightness: number;
  frp: number;
  confidence: number;
  satellite: string;
}

export interface SatelliteValidation {
  id: number;
  hotspot_id: number;
  status: "CONFIRMED" | "LIKELY" | "UNCERTAIN" | "NOT VALIDATED";
  provider: string;
  smoke_indication: boolean | null;
  burn_area_ha: number | null;
  fire_extent_km2: number | null;
  ndvi_before: number | null;
  ndvi_after: number | null;
  notes?: string;
  validated_at?: string;
}

export interface Explanation {
  top_class?: string;
  confidence?: number;
  model_derived_factors: Record<string, string>;
  contextual_factors?: string[];
  reasoning?: string;
  probability_gap_pct?: number;
  runner_up?: string;
}

export interface AlertItem {
  id: number;
  code: string;
  hotspot_id: number | null;
  hotspot_code?: string | null;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  location: string;
  confidence: number;
  risk_score: number;
  status: "new" | "acknowledged" | "investigating" | "escalated" | "resolved" | string;
  assigned_officer: string;
  recommended_action: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface IndustrialZone {
  id: number;
  code: string;
  name: string;
  zone_type: string;
  latitude: number;
  longitude: number;
  state: string;
  district: string;
  radius_km: number;
  risk_level: RiskLevel | string;
  monitoring_level: string;
  population_exposure: number;
  description: string;
}

export interface ZoneIntelligence {
  zone: IndustrialZone;
  hotspots_1km: number;
  hotspots_5km: number;
  historical_activity: number;
  alerts: number;
  population_exposure: number;
  road_access: string;
  recommended_monitoring: string;
  hotspots_1km_list: Hotspot[];
  hotspots_5km_list: Hotspot[];
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  severity: string;
  entity: string;
  entity_id: string;
  read: boolean;
  created_at: string;
}

export interface SystemHealth {
  overall: string;
  demo_mode: boolean;
  checked_at: string;
  components: {
    name: string;
    status: string;
    mode: string;
    latency_ms: number;
    detail: string;
    last_sync?: string | null;
  }[];
}

export interface ScenarioResult {
  scenario: string;
  completed: boolean;
  persistent_hotspot: Hotspot;
  hotspot: Hotspot;
  alert: AlertItem;
  zone: IndustrialZone;
  risk_trend: number[];
  steps: {
    phase: number;
    title: string;
    detail: string;
    risk_score: number;
    classification: string;
  }[];
}

export interface IngestResult {
  provider: string;
  mode: string;
  records_received: number;
  hotspots_created: number;
  hotspots_updated: number;
  alerts_created: number;
  duration_ms: number;
  errors: string[];
}

export interface CopilotResponse {
  answer: string;
  mode: string;
  intents: string[];
  data?: Record<string, unknown>;
}

export interface AnalyticsData {
  by_classification: { name: string; value: number }[];
  by_state: { name: string; value: number }[];
  by_district: { name: string; value: number }[];
  by_risk: { name: string; value: number }[];
  daily: { label: string; count: number }[];
  weekly: { label: string; count: number }[];
  monthly: { label: string; count: number }[];
  classification_series: Record<string, number | string>[];
  industrial_vs_wildfire: { date: string; industrial: number; wildfire: number }[];
  top_industrial_zones: { name: string; type: string; risk_level: string; monitoring: string }[];
  top_recurring_hotspots: { code: string; persistence_score: number; classification: string; state: string }[];
  avg_classification_confidence: number;
  avg_risk_score: number;
  alert_status: Record<string, number>;
  generated_at: string;
}

export interface HotspotStats {
  total: number;
  by_risk: Record<string, number>;
  by_classification: Record<string, number>;
  critical: number;
  high: number;
  industrial_fires: number;
  wildfires: number;
  agricultural_burns: number;
  persistent_sources: number;
  week_change_pct: number;
  industrial_fire_change_pct: number;
}

export interface GeoJson {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}

export interface GeoJsonFeature {
  type: "Feature";
  geometry: { type: string; coordinates: number[] };
  properties: Record<string, unknown>;
}