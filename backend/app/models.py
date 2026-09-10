"""FIRE-X database models.

Spatial storage strategy (works on SQLite and Postgres/PostGIS):
- latitude/longitude are indexed float columns
- geometry is stored as WKT (EPSG:4326) - PostGIS-ready when Postgres is used
- nearest-* distance features are precomputed into ``infrastructure_features``
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")  # admin|analyst|field|viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # HX-0001
    external_id = Column(String(100), index=True)  # FIRMS scan id
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    geometry = Column(Text)  # WKT POINT(lng lat)
    acquisition_time = Column(DateTime, nullable=False, index=True)
    brightness = Column(Float, default=0.0)  # Kelvin
    frp = Column(Float, default=0.0)  # MW
    confidence = Column(Float, default=0.0)  # 0..1
    source = Column(String(50), default="firms")  # firms|demo|scenario
    satellite = Column(String(50), default="VIIRS S-NPP")
    daynight = Column(String(10), default="D")

    classification = Column(String(60), default="Other Thermal Anomaly")
    classification_confidence = Column(Float, default=0.0)
    probabilities = Column(JSON, default=dict)

    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="LOW")
    persistence_score = Column(Float, default=0.0)
    temporal_pattern = Column(String(30), default="unknown")
    status = Column(String(30), default="active")  # active|monitoring|resolved|dismissed
    state = Column(String(60), default="")
    district = Column(String(60), default="")
    land_cover = Column(String(30), default="Other")

    explanation = Column(JSON, default=dict)
    feature_vector = Column(JSON, default=list)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    features = relationship("InfrastructureFeature", back_populates="hotspot", uselist=False)
    history = relationship(
        "HistoricalDetection",
        back_populates="hotspot",
        order_by="HistoricalDetection.detection_time",
    )
    validations = relationship("SatelliteValidation", back_populates="hotspot")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "external_id": self.external_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "acquisition_time": self.acquisition_time.isoformat() if self.acquisition_time else None,
            "brightness": self.brightness,
            "frp": self.frp,
            "confidence": self.confidence,
            "source": self.source,
            "satellite": self.satellite,
            "classification": self.classification,
            "classification_confidence": self.classification_confidence,
            "probabilities": self.probabilities or {},
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "persistence_score": self.persistence_score,
            "temporal_pattern": self.temporal_pattern,
            "status": self.status,
            "state": self.state,
            "district": self.district,
            "land_cover": self.land_cover,
            "explanation": self.explanation or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InfrastructureFeature(Base):
    __tablename__ = "infrastructure_features"

    id = Column(Integer, primary_key=True)
    hotspot_id = Column(Integer, ForeignKey("hotspots.id"), unique=True, index=True, nullable=False)

    nearest_refinery_distance = Column(Float, default=-1.0)
    nearest_factory_distance = Column(Float, default=-1.0)
    nearest_powerplant_distance = Column(Float, default=-1.0)
    nearest_mine_distance = Column(Float, default=-1.0)
    nearest_forest_distance = Column(Float, default=-1.0)
    nearest_agriculture_distance = Column(Float, default=-1.0)
    nearest_settlement_distance = Column(Float, default=-1.0)
    nearest_road_distance = Column(Float, default=-1.0)
    nearest_railway_distance = Column(Float, default=-1.0)
    nearest_pipeline_distance = Column(Float, default=-1.0)

    nearest_refinery_id = Column(String(100), default="")
    nearest_factory_id = Column(String(100), default="")
    nearest_powerplant_id = Column(String(100), default="")
    nearest_mine_id = Column(String(100), default="")
    nearest_forest_id = Column(String(100), default="")
    nearest_agriculture_id = Column(String(100), default="")
    nearest_settlement_id = Column(String(100), default="")

    hotspot = relationship("Hotspot", back_populates="features")

    def to_dict(self) -> dict:
        return {
            "nearest_refinery_distance": self.nearest_refinery_distance,
            "nearest_factory_distance": self.nearest_factory_distance,
            "nearest_powerplant_distance": self.nearest_powerplant_distance,
            "nearest_mine_distance": self.nearest_mine_distance,
            "nearest_forest_distance": self.nearest_forest_distance,
            "nearest_agriculture_distance": self.nearest_agriculture_distance,
            "nearest_settlement_distance": self.nearest_settlement_distance,
            "nearest_road_distance": self.nearest_road_distance,
            "nearest_railway_distance": self.nearest_railway_distance,
            "nearest_pipeline_distance": self.nearest_pipeline_distance,
            "nearest_refinery_id": self.nearest_refinery_id,
            "nearest_factory_id": self.nearest_factory_id,
            "nearest_powerplant_id": self.nearest_powerplant_id,
            "nearest_mine_id": self.nearest_mine_id,
            "nearest_forest_id": self.nearest_forest_id,
            "nearest_agriculture_id": self.nearest_agriculture_id,
            "nearest_settlement_id": self.nearest_settlement_id,
        }


class Infrastructure(Base):
    """Infrastructure assets used for proximity analysis (points)."""
    __tablename__ = "infrastructure"

    id = Column(Integer, primary_key=True)
    code = Column(String(40), unique=True, index=True)
    name = Column(String(255), nullable=False)
    infra_type = Column(String(40), index=True, nullable=False)  # refinery|factory|power_plant|mine|settlement
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    state = Column(String(60), default="")
    district = Column(String(60), default="")
    zone_id = Column(Integer, ForeignKey("industrial_zones.id"), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "infra_type": self.infra_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "state": self.state,
            "district": self.district,
            "zone_id": self.zone_id,
        }


class HistoricalDetection(Base):
    __tablename__ = "historical_detections"
    __table_args__ = (UniqueConstraint("hotspot_id", "detection_time", name="uq_hotspot_time"),)

    id = Column(Integer, primary_key=True)
    hotspot_id = Column(Integer, ForeignKey("hotspots.id"), index=True, nullable=False)
    detection_time = Column(DateTime, index=True, nullable=False)
    brightness = Column(Float, default=0.0)
    frp = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    satellite = Column(String(50), default="VIIRS S-NPP")

    hotspot = relationship("Hotspot", back_populates="history")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "detection_time": self.detection_time.isoformat() if self.detection_time else None,
            "brightness": self.brightness,
            "frp": self.frp,
            "confidence": self.confidence,
            "satellite": self.satellite,
        }


class IndustrialZone(Base):
    __tablename__ = "industrial_zones"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, index=True)
    name = Column(String(255), nullable=False)
    zone_type = Column(String(60), default="Industrial Park")  # Refinery|Factory|Power Plant|Mine|Industrial Park
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    state = Column(String(60), default="")
    district = Column(String(60), default="")
    radius_km = Column(Float, default=5.0)
    risk_level = Column(String(20), default="LOW")
    monitoring_level = Column(String(30), default="ROUTINE")
    population_exposure = Column(Integer, default=0)
    description = Column(Text, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "zone_type": self.zone_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "state": self.state,
            "district": self.district,
            "radius_km": self.radius_km,
            "risk_level": self.risk_level,
            "monitoring_level": self.monitoring_level,
            "population_exposure": self.population_exposure,
            "description": self.description,
        }


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, index=True)
    hotspot_id = Column(Integer, ForeignKey("hotspots.id"), index=True, nullable=True)
    alert_type = Column(String(60), default="risk")  # risk|industrial_fire|persistent|sudden_high_intensity
    severity = Column(String(20), default="MODERATE")
    title = Column(String(255), default="")
    message = Column(Text, default="")
    location = Column(String(120), default="")
    confidence = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    status = Column(String(30), default="new")  # new|acknowledged|investigating|escalated|resolved
    assigned_officer = Column(String(120), default="")
    recommended_action = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    hotspot = relationship("Hotspot")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "hotspot_id": self.hotspot_id,
            "hotspot_code": self.hotspot.code if self.hotspot else None,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "location": self.location,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "status": self.status,
            "assigned_officer": self.assigned_officer,
            "recommended_action": self.recommended_action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SatelliteValidation(Base):
    __tablename__ = "satellite_validations"

    id = Column(Integer, primary_key=True)
    hotspot_id = Column(Integer, ForeignKey("hotspots.id"), index=True, nullable=False)
    status = Column(String(30), default="NOT VALIDATED")  # CONFIRMED|LIKELY|UNCERTAIN|NOT VALIDATED
    provider = Column(String(50), default="demo")  # demo|sentinel2|landsat
    smoke_indication = Column(Boolean, nullable=True)
    burn_area_ha = Column(Float, nullable=True)
    fire_extent_km2 = Column(Float, nullable=True)
    ndvi_before = Column(Float, nullable=True)
    ndvi_after = Column(Float, nullable=True)
    imagery_before = Column(Text, default="")
    imagery_after = Column(Text, default="")
    notes = Column(Text, default="")
    validated_at = Column(DateTime, default=utcnow)

    hotspot = relationship("Hotspot", back_populates="validations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hotspot_id": self.hotspot_id,
            "status": self.status,
            "provider": self.provider,
            "smoke_indication": self.smoke_indication,
            "burn_area_ha": self.burn_area_ha,
            "fire_extent_km2": self.fire_extent_km2,
            "ndvi_before": self.ndvi_before,
            "ndvi_after": self.ndvi_after,
            "imagery_before": self.imagery_before,
            "imagery_after": self.imagery_after,
            "notes": self.notes,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
        }


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    user = Column(String(120), default="system")
    action = Column(String(80), index=True)
    entity = Column(String(80), default="")
    entity_id = Column(String(80), default="")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user": self.user,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "details": self.details or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    title = Column(String(255), default="")
    message = Column(Text, default="")
    severity = Column(String(20), default="info")
    entity = Column(String(80), default="")
    entity_id = Column(String(80), default="")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "read": self.read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }