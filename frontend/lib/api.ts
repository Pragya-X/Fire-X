/**
 * FIRE-X typed API client.
 * All backend calls go through this module - components never scatter fetch calls.
 */
import type {
  AlertItem,
  AnalyticsData,
  CopilotResponse,
  GeoJson,
  Hotspot,
  HotspotDetail,
  HotspotStats,
  IndustrialZone,
  IngestResult,
  LoginResponse,
  NotificationItem,
  PlaybackFrame,
  ScenarioResult,
  SystemHealth,
  User,
  ZoneIntelligence,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("firex_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("firex_token", token);
  else localStorage.removeItem("firex_token");
}

async function request<T>(path: string, options: RequestInit = {}, auth = true): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_URL}${path}`, { ...options, headers, cache: "no-store" });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* keep default */
    }
    if (res.status === 401) {
      setToken(null);
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function blobRequest(path: string): Promise<Blob> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetch(`${API_URL}${path}`, { headers }).then((res) => {
    if (!res.ok) throw new ApiError(res.status, "Download failed");
    return res.blob();
  });
}

// ---------------------------------------------------------------- auth
export const login = (email: string, password: string) =>
  request<LoginResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }, false);
export const getMe = () => request<User>("/api/v1/auth/me");
export const changePassword = (current_password: string, new_password: string) =>
  request<{ ok: boolean }>("/api/v1/auth/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password, new_password }),
  });
export const forgotPassword = (email: string) =>
  request<{ ok: boolean }>("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  }, false);
export const resetPassword = (token: string, new_password: string) =>
  request<{ ok: boolean }>("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password }),
  }, false);

// ---------------------------------------------------------------- hotspots
export interface HotspotQuery {
  page?: number;
  page_size?: number;
  classification?: string;
  risk?: string;
  min_confidence?: number;
  state?: string;
  district?: string;
  status?: string;
  temporal_pattern?: string;
  date_from?: string;
  date_to?: string;
  industrial_proximity?: number;
  forest_proximity?: number;
  agriculture_proximity?: number;
  settlement_proximity?: number;
  search?: string;
  sort?: string;
  order?: string;
}

export const getHotspots = (q: HotspotQuery = {}) => {
  const params = new URLSearchParams();
  Object.entries(q).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") params.set(k, String(v));
  });
  return request<{ items: Hotspot[]; total: number; page: number; page_size: number }>(
    `/api/v1/hotspots?${params.toString()}`
  );
};

export const getHotspot = (id: number | string) => request<HotspotDetail>(`/api/v1/hotspots/${id}`);
export const getHotspotsGeojson = (filters: Record<string, string> = {}) => {
  const params = new URLSearchParams(filters);
  return request<GeoJson>(`/api/v1/hotspots/geojson?${params.toString()}`);
};
export const getHotspotStats = () => request<HotspotStats>("/api/v1/hotspots/stats");
export const downloadExport = (format: "csv" | "json" | "geojson" | "pdf", filters: Record<string, string> = {}) => {
  const params = new URLSearchParams({ format, ...filters });
  return blobRequest(`/api/v1/hotspots/export?${params.toString()}`);
};
export const downloadHotspotReport = (id: number) => blobRequest(`/api/v1/hotspots/${id}/report`);
export const downloadDailyReport = () => blobRequest("/api/v1/reports/daily");
export const downloadZoneReport = (id: number) => blobRequest(`/api/v1/reports/zone/${id}`);

// ---------------------------------------------------------------- infrastructure
export const getInfrastructure = () => request<{ items: unknown[]; total: number }>("/api/v1/infrastructure");
export const getInfrastructureGeojson = (infraType?: string) =>
  request<GeoJson>(
    `/api/v1/infrastructure/geojson${infraType ? `?infra_type=${infraType}` : ""}`
  );
export const getNetworkGeojson = () => request<GeoJson>("/api/v1/infrastructure/network/geojson");
export const getLandcoverGeojson = () => request<GeoJson>("/api/v1/infrastructure/landcover/geojson");

// ---------------------------------------------------------------- industrial zones
export const getIndustrialZones = () => request<{ items: IndustrialZone[]; total: number }>("/api/v1/industrial-zones");
export const getZone = (id: number) => request<ZoneIntelligence>(`/api/v1/industrial-zones/${id}`);
export const getZonesGeojson = () => request<GeoJson>("/api/v1/industrial-zones/geojson");

// ---------------------------------------------------------------- alerts
export const getAlerts = (q: Record<string, string> = {}) => {
  const params = new URLSearchParams(q);
  return request<{ items: AlertItem[]; total: number }>(`/api/v1/alerts?${params.toString()}`);
};
export const acknowledgeAlert = (id: number) => request<AlertItem>(`/api/v1/alerts/${id}/acknowledge`, { method: "POST" });
export const escalateAlert = (id: number) => request<AlertItem>(`/api/v1/alerts/${id}/escalate`, { method: "POST" });
export const resolveAlert = (id: number) => request<AlertItem>(`/api/v1/alerts/${id}/resolve`, { method: "POST" });
export const getNotifications = () => request<{ items: NotificationItem[]; unread: number }>("/api/v1/alerts/notifications");
export const markNotificationsRead = () => request<{ ok: boolean }>("/api/v1/alerts/notifications/mark-read", { method: "POST" });
export const markNotificationRead = (id: number) =>
  request<{ ok: boolean }>(`/api/v1/alerts/notifications/${id}/read`, { method: "POST" });

// ---------------------------------------------------------------- analytics / historical
export const getAnalytics = () => request<AnalyticsData>("/api/v1/analytics");
export const getHistorical = (q: Record<string, string> = {}) => {
  const params = new URLSearchParams(q);
  return request<{ items: Hotspot[]; total: number }>(`/api/v1/historical?${params.toString()}`);
};
export const getPlayback = (days = 14) => request<{ frames: PlaybackFrame[] }>(`/api/v1/historical/playback?days=${days}`);
export const getRecurring = () => request<{ items: Hotspot[]; total: number }>("/api/v1/historical/recurring");
export const getTimeline = (days = 30) => request<{ timeline: { date: string; count: number }[] }>(`/api/v1/historical/timeline?days=${days}`);


// ---------------------------------------------------------------- ML / ingest / satellite
export const classifyHotspot = (hotspotId: number) =>
  request<{
    hotspot_id: number;
    hotspot_code: string;
    classification: string;
    confidence: number;
    probabilities: Record<string, number>;
    feature_importance: Record<string, number>;
    feature_importance_type: string;
    model_mode: string;
    model_version: string;
    risk_score: number;
    risk_level: string;
    explanation: Record<string, unknown>;
  }>("/api/v1/ml/classify", { method: "POST", body: JSON.stringify({ hotspot_id: hotspotId }) });

export const getMlStatus = () => request<{ online: boolean; status: string; mode: string; model_version: string; training_data_type: string; evaluation?: unknown }>("/api/v1/ml/status");

export const ingestFirms = () => request<IngestResult>("/api/v1/ingest/firms", { method: "POST" });
export const ingestDemo = () => request<IngestResult>("/api/v1/ingest/demo", { method: "POST" });
export const ingestOsm = () => request<IngestResult>("/api/v1/ingest/osm", { method: "POST" });
export const ingestLandcover = () => request<IngestResult>("/api/v1/ingest/landcover", { method: "POST" });
export const refreshAnalysis = () => request<{ updated: number; duration_ms: number }>("/api/v1/ingest/refresh-analysis", { method: "POST" });
export const recalculateRisk = () => request<{ updated: number; duration_ms: number }>("/api/v1/ingest/recalculate-risk", { method: "POST" });
export const validateSatellite = (hotspotId: number) =>
  request<{ status: string; provider: string; duration_ms: number }>("/api/v1/ingest/satellite/validate", {
    method: "POST",
    body: JSON.stringify({ hotspot_id: hotspotId }),
  });
export const getValidations = () => request<{ items: unknown[]; total: number }>("/api/v1/satellite/validations");

// ---------------------------------------------------------------- scenario / copilot / health
export const runDemoScenario = () => request<ScenarioResult>("/api/v1/scenario/run", { method: "POST" });
export const getScenarioState = () => request<{ scenario_available: boolean; hotspot: Hotspot | null; zone: IndustrialZone | null; alert: AlertItem | null }>("/api/v1/scenario/state");

export const askCopilot = (question: string) =>
  request<CopilotResponse>("/api/v1/copilot/ask", { method: "POST", body: JSON.stringify({ question }) });
export const getCopilotSuggestions = () => request<{ items: string[] }>("/api/v1/copilot/suggestions");

export const getSystemHealth = () => request<SystemHealth>("/api/v1/system-health");
export const getActivity = () => request<{ items: unknown[]; total: number }>("/api/v1/activity");

// SSE stream URL helper
export const streamUrl = () => `${API_URL}/api/v1/events/stream`;
// Reviewed observation events are isolated from seeded demonstration hotspots.
export interface EventIntelligence {
  decision: string; confidence: number | null; confidence_type: string; mode: string; reasons: string[];
  anomaly: { status: string; score: number | null; deviation_mw: number | null; historical_mean_mw: number | null; reason: string };
  persistence: { status: string; observed_recurrence: number | null; coefficient_of_variation: number | null; reason: string };
  explanation: { shap: { available: boolean; reason?: string; features?: string[]; values?: number[][]; classes?: string[] } };
}
export interface ThermalEvent {
  event_id: string; latitude: number; longitude: number; start_time: string; end_time: string;
  facility_id: string | null; features: Record<string, string | number | boolean | null>;
  provenance: Record<string, unknown>; intelligence: EventIntelligence | null;
}
export interface EventAnnotation {
  event_id: string; label: string; review_status: string; annotator: string; reviewer: string | null;
  confidence: number | null; quality: "A" | "B" | "C"; evidence: string[]; source: string; notes: string;
}
export interface EventDetail extends ThermalEvent {
  observations: Record<string, string | number | null>[];
  annotations: { revision: number; actor_id: number; annotation: EventAnnotation }[];
}
export const getEventStatus = () => request<{ event_count: number; model_mode: string; training_ready: boolean; reason: string; classes: string[] }>("/api/v1/thermal-events/status");
export const getThermalEvents = (query: Record<string, string> = {}) => request<{ items: ThermalEvent[]; total: number }>(`/api/v1/thermal-events?${new URLSearchParams(query)}`);
export const getThermalEvent = (id: string) => request<EventDetail>(`/api/v1/thermal-events/${encodeURIComponent(id)}`);
export const getEventFacility = (id: string) => request<{ events: ThermalEvent[]; association_note: string }>(`/api/v1/thermal-events/facilities/${encodeURIComponent(id)}`);
export const exportEventAnnotations = () => request<EventAnnotation[]>("/api/v1/thermal-events/annotations/export");
export const saveEventAnnotation = (id: string, body: { expected_revision: number; action: "save" | "submit" | "approve" | "reject"; label: string; confidence: number | null; quality: "A" | "B" | "C"; evidence: string[]; source: string; notes: string }) =>
  request<{ revision: number; annotation: EventAnnotation; training_eligible: boolean }>(`/api/v1/thermal-events/${encodeURIComponent(id)}/annotations`, { method: "POST", body: JSON.stringify(body) });
export const getEventExplanation = (id: string) => request<EventIntelligence>(`/api/v1/thermal-events/${encodeURIComponent(id)}/explanation?shap=true`);
