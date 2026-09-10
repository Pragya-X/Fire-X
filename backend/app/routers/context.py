"""Read-only facility, zone and satellite context."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.gis.engine import geojson_points, haversine_km
from app.models import Infrastructure, Hotspot, IndustrialZone, SatelliteValidation
from app.providers.osm import load_landcover_geojson, load_network_geojson
from app.schemas import IndustrialZoneOut


router = APIRouter(prefix="/api/v1")


@router.get("/infrastructure", tags=['infrastructure'], response_model=dict)
def list_infrastructure(
    infra_type: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Infrastructure)
    if infra_type:
        q = q.filter(Infrastructure.infra_type == infra_type)
    if state:
        q = q.filter(Infrastructure.state == state)
    items = q.all()
    return {"items": [i.to_dict() for i in items], "total": len(items)}


@router.get("/infrastructure/geojson", tags=['infrastructure'])
def infrastructure_geojson(
    infra_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Infrastructure)
    if infra_type:
        q = q.filter(Infrastructure.infra_type == infra_type)
    items = [i.to_dict() for i in q.all()]
    return geojson_points(items, props=("id", "code", "name", "infra_type", "state", "district"))


@router.get("/infrastructure/network/geojson", tags=['infrastructure'])
def network_geojson():
    """Roads, railways and pipelines."""
    return load_network_geojson()


@router.get("/infrastructure/landcover/geojson", tags=['infrastructure'])
def landcover_geojson():
    """Forest and agriculture polygons."""
    return load_landcover_geojson()


def _zone_intelligence(db: Session, zone: IndustrialZone) -> dict:
    hotspots = db.query(Hotspot).all()
    within_1km = [h for h in hotspots if haversine_km(zone.latitude, zone.longitude, h.latitude, h.longitude) <= 1.0]
    within_5km = [h for h in hotspots if haversine_km(zone.latitude, zone.longitude, h.latitude, h.longitude) <= 5.0]
    historical_activity = sum(len(h.history) for h in within_5km)
    from app.models import Alert

    alerts = db.query(Alert).filter(Alert.hotspot_id.in_([h.id for h in within_5km])).count() if within_5km else 0
    return {
        "zone": zone.to_dict(),
        "hotspots_1km": len(within_1km),
        "hotspots_5km": len(within_5km),
        "historical_activity": historical_activity,
        "alerts": alerts,
        "population_exposure": zone.population_exposure,
        "road_access": "Good" if zone.monitoring_level != "INTENSIVE" else "Restricted access possible",
        "recommended_monitoring": zone.monitoring_level,
        "hotspots_1km_list": [h.to_dict() for h in sorted(within_1km, key=lambda h: h.risk_score, reverse=True)[:20]],
        "hotspots_5km_list": [h.to_dict() for h in sorted(within_5km, key=lambda h: h.risk_score, reverse=True)[:20]],
    }


@router.get("/industrial-zones", tags=['industrial-zones'], response_model=dict)
def list_zones(zone_type: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(IndustrialZone)
    if zone_type:
        q = q.filter(IndustrialZone.zone_type == zone_type)
    items = q.order_by(IndustrialZone.risk_level.desc()).all()
    return {"items": [IndustrialZoneOut.model_validate(z).model_dump() for z in items], "total": len(items)}


@router.get("/industrial-zones/geojson", tags=['industrial-zones'])
def zones_geojson(db: Session = Depends(get_db)):
    zones = db.query(IndustrialZone).all()
    features = []
    for z in zones:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [z.longitude, z.latitude]},
                "properties": {
                    "id": z.id, "code": z.code, "name": z.name, "zone_type": z.zone_type,
                    "state": z.state, "district": z.district, "risk_level": z.risk_level,
                    "monitoring_level": z.monitoring_level, "radius_km": z.radius_km,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


@router.get("/industrial-zones/{zone_id}", tags=['industrial-zones'], response_model=dict)
def zone_detail(zone_id: int, db: Session = Depends(get_db)):
    z = db.get(IndustrialZone, zone_id)
    if z is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return _zone_intelligence(db, z)


@router.get("/satellite/validations", tags=['satellite'], response_model=dict)
def list_validations(
    status: Optional[str] = None,
    hotspot_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(SatelliteValidation)
    if status:
        q = q.filter(SatelliteValidation.status == status)
    if hotspot_id:
        q = q.filter(SatelliteValidation.hotspot_id == hotspot_id)
    items = q.order_by(SatelliteValidation.validated_at.desc()).limit(limit).all()
    return {"items": [v.to_dict() for v in items], "total": len(items)}
