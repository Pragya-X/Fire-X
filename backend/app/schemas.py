"""Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "viewer"  # viewer|field|analyst|admin


# ---------- Hotspots ----------
class HotspotOut(BaseModel):
    id: int
    code: str
    external_id: Optional[str] = None
    latitude: float
    longitude: float
    acquisition_time: Optional[datetime] = None
    brightness: float = 0.0
    frp: float = 0.0
    confidence: float = 0.0
    source: str = "firms"
    satellite: str = "VIIRS S-NPP"
    classification: str = "Other Thermal Anomaly"
    classification_confidence: float = 0.0
    probabilities: dict[str, float] = {}
    risk_score: float = 0.0
    risk_level: str = "LOW"
    persistence_score: float = 0.0
    temporal_pattern: str = "unknown"
    status: str = "active"
    state: str = ""
    district: str = ""
    land_cover: str = "Other"
    explanation: dict[str, Any] = {}
    features: Optional[Any] = Field(default=None, exclude=True)  # injected manually as dict

    model_config = {"from_attributes": True}


class HotspotDetailOut(HotspotOut):
    feature_vector: list = []
    history: Any = Field(default_factory=list, exclude=True)  # injected manually as list[dict]
    validations: Any = Field(default_factory=list, exclude=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------- Industrial zones ----------
class IndustrialZoneOut(BaseModel):
    id: int
    code: str
    name: str
    zone_type: str
    latitude: float
    longitude: float
    state: str = ""
    district: str = ""
    radius_km: float = 5.0
    risk_level: str = "LOW"
    monitoring_level: str = "ROUTINE"
    population_exposure: int = 0
    description: str = ""

    model_config = {"from_attributes": True}


# ---------- Alerts ----------
class AlertOut(BaseModel):
    id: int
    code: str
    hotspot_id: Optional[int] = None
    hotspot_code: Optional[str] = None
    alert_type: str = "risk"
    severity: str = "MODERATE"
    title: str = ""
    message: str = ""
    location: str = ""
    confidence: float = 0.0
    risk_score: float = 0.0
    status: str = "new"
    assigned_officer: str = ""
    recommended_action: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    assigned_officer: Optional[str] = None


# ---------- ML ----------
class ClassifyRequest(BaseModel):
    hotspot_id: int


class ClassificationOut(BaseModel):
    model_mode: str = "RULES"
    model_version: str = "rules-v1"
    training_data_type: str = "none"
    requested_mode: str = "rules"
    fallback_reason: Optional[str] = None
    feature_importance_type: str = "heuristic_weights"
    hotspot_id: int
    hotspot_code: str
    classification: str
    confidence: float
    probabilities: dict[str, float]
    feature_importance: dict[str, float]
    risk_score: float
    risk_level: str
    explanation: dict[str, Any]


# ---------- Copilot ----------
class CopilotRequest(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    answer: str
    mode: str  # "demo" | "llm"
    intents: list[str] = []
    data: Optional[dict[str, Any]] = None


# ---------- Scenario ----------
class ScenarioStep(BaseModel):
    phase: int
    title: str
    detail: str
    risk_score: float
    classification: str
    hotspot_code: str


class ScenarioRunResponse(BaseModel):
    scenario: str
    completed: bool
    steps: list[ScenarioStep]
    hotspot: HotspotDetailOut
    alert: Optional[AlertOut] = None
    zone: Optional[IndustrialZoneOut] = None


# ---------- Ingest ----------
class IngestResult(BaseModel):
    provider: str
    mode: str  # live | demo
    records_received: int
    hotspots_created: int
    hotspots_updated: int
    alerts_created: int
    duration_ms: int
    errors: list[str] = []


# ---------- Health ----------
class ComponentHealth(BaseModel):
    name: str
    status: str  # operational | degraded | offline | demo
    mode: str = ""
    latency_ms: float = 0.0
    detail: str = ""
    last_sync: Optional[str] = None


# ---------- Export ----------
class ExportResponse(BaseModel):
    filename: str
    format: str
    count: int