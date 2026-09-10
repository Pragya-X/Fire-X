"""Auditable event store, separate from seeded legacy demonstration hotspots."""
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, UniqueConstraint, Text
from app.database import Base
from app.models import utcnow

class ThermalEvent(Base):
    __tablename__='thermal_events'
    event_id=Column(String(100),primary_key=True)
    latitude=Column(Float,nullable=False,index=True)
    longitude=Column(Float,nullable=False,index=True)
    start_time=Column(DateTime(timezone=True),nullable=False,index=True)
    end_time=Column(DateTime(timezone=True),nullable=False,index=True)
    facility_id=Column(String(255),nullable=True,index=True)
    dataset_sha256=Column(String(64),nullable=False,index=True)
    features=Column(JSON,nullable=False)
    provenance=Column(JSON,nullable=False)
    imported_at=Column(DateTime(timezone=True),default=utcnow,nullable=False)

class EventPrediction(Base):
    __tablename__='event_predictions'
    id=Column(Integer,primary_key=True)
    event_id=Column(String(100),ForeignKey('thermal_events.event_id'),nullable=False,index=True)
    model_version=Column(String(255),nullable=False)
    decision=Column(String(100),nullable=False,index=True)
    confidence=Column(Float,nullable=True)
    intelligence=Column(JSON,nullable=False)  # anomaly, persistence, risk and reasons
    created_at=Column(DateTime(timezone=True),default=utcnow,nullable=False)

class EventAnnotation(Base):
    __tablename__='event_annotations'
    id=Column(Integer,primary_key=True)
    event_id=Column(String(100),ForeignKey('thermal_events.event_id'),nullable=False,index=True)
    revision=Column(Integer,nullable=False)
    actor_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    payload=Column(JSON,nullable=False)
    created_at=Column(DateTime(timezone=True),default=utcnow,nullable=False)
    __table_args__=(UniqueConstraint('event_id','revision',name='uq_annotation_revision'),)

class ThermalObservation(Base):
    __tablename__='thermal_observations'
    detection_id=Column(String(100),primary_key=True)
    event_id=Column(String(100),ForeignKey('thermal_events.event_id'),nullable=False,index=True)
    latitude=Column(Float,nullable=False,index=True)
    longitude=Column(Float,nullable=False,index=True)
    acquisition_time=Column(DateTime(timezone=True),nullable=False,index=True)
    measurements=Column(JSON,nullable=False)

class ReferenceFacility(Base):
    __tablename__='reference_facilities'
    facility_id=Column(String(255),primary_key=True)
    name=Column(String(1000),nullable=False)
    facility_type=Column(String(100),nullable=False,index=True)
    latitude=Column(Float,nullable=False)
    longitude=Column(Float,nullable=False)
    geometry_wkt=Column(Text,nullable=False)
    provenance=Column(JSON,nullable=False)
