"""OpenStreetMap infrastructure ingestion.

- ``OsmProvider`` queries the Overpass API for industrial infrastructure when
  the Overpass endpoint is reachable.
- ``SeededOsmProvider`` returns the built-in India infrastructure dataset so
  the frontend never depends directly on Overpass availability.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Infrastructure

OVERPASS_QUERY = """
[out:json][timeout:25];
(
  nwr["industrial"="refinery"]({bbox});
  nwr["industrial"="factory"]({bbox});
  nwr["power"="plant"]({bbox});
  nwr["landuse"="industrial"]({bbox});
  nwr["man_made"="mine"]({bbox});
);
out center 1000;
"""


class OsmProviderUnavailable(Exception):
    pass


class OsmProvider:
    name = "OpenStreetMap"
    mode = "live"

    def fetch(self, bbox: str = "8.0,68.0,37.0,97.0") -> list[dict]:
        query = OVERPASS_QUERY.format(bbox=bbox)
        try:
            resp = httpx.post(settings.OVERPASS_API_URL, data={"data": query}, timeout=40)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            raise OsmProviderUnavailable(f"Overpass request failed: {exc}") from exc
        out = []
        for el in data.get("elements", []):
            lat = el.get("lat") or (el.get("center") or {}).get("lat")
            lon = el.get("lon") or (el.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            tags = el.get("tags", {})
            out.append(
                {
                    "name": tags.get("name") or tags.get("ref") or f"OSM feature {el['id']}",
                    "infra_type": "refinery" if tags.get("industrial") == "refinery"
                    else "factory" if tags.get("industrial") == "factory"
                    else "power_plant" if tags.get("power") == "plant"
                    else "industrial_area" if tags.get("landuse") == "industrial"
                    else "mine",
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "state": tags.get("addr:state", ""),
                    "district": tags.get("addr:district", ""),
                }
            )
        return out


class SeededOsmProvider:
    name = "OpenStreetMap"
    mode = "demo"

    def fetch(self, db: Session, bbox: str = "") -> list[dict]:
        rows = db.query(Infrastructure).all()
        return [r.to_dict() for r in rows]


def get_osm_provider(db: Optional[Session] = None):
    """Prefer Overpass when reachable, else the seeded dataset."""
    if settings.OVERPASS_API_URL and settings.ENV == "production":
        return OsmProvider()
    return SeededOsmProvider()


def load_network_geojson() -> dict:
    path = Path(settings.DATA_DIR) / "network.geojson"
    if path.exists():
        return json.loads(path.read_text())
    return {"type": "FeatureCollection", "features": []}


def load_landcover_geojson() -> dict:
    path = Path(settings.DATA_DIR) / "landcover.geojson"
    if path.exists():
        return json.loads(path.read_text())
    return {"type": "FeatureCollection", "features": []}

def reference_features(document: dict) -> tuple[dict, dict]:
    """Convert a user-supplied Overpass export; never guess an unknown facility.

    Closed way geometry is retained. Centers are explicitly point approximations.
    Relations needing ring assembly must be supplied as properly assembled GeoJSON.
    """
    if not isinstance(document.get('elements'), list):
        raise ValueError('Expected Overpass JSON elements')
    features, rejected = [], []
    for index, element in enumerate(document['elements']):
        fid = f"{element.get('type', 'unknown')}/{element.get('id', index)}"
        tags = element.get('tags') or {}
        category = (
            'refinery' if tags.get('industrial') == 'refinery' else
            'factory' if tags.get('industrial') == 'factory' else
            'power_plant' if tags.get('power') == 'plant' else
            'mine' if tags.get('man_made') == 'mine' else
            'industrial_area' if tags.get('landuse') == 'industrial' else None)
        if category is None:
            rejected.append({'facility_id':fid, 'reason':'UNKNOWN_FACILITY_TYPE', 'tags':tags})
            continue
        coordinates = element.get('geometry')
        representation = 'geometry'
        if coordinates and element.get('type') == 'way':
            ring = [[p['lon'], p['lat']] for p in coordinates]
            if len(ring) < 4 or ring[0] != ring[-1]:
                rejected.append({'facility_id':fid, 'reason':'OPEN_WAY_REQUIRES_EXPLICIT_GEOMETRY'})
                continue
            geometry = {'type':'Polygon', 'coordinates':[ring]}
        elif 'lat' in element and 'lon' in element:
            geometry = {'type':'Point', 'coordinates':[element['lon'],element['lat']]}
        elif element.get('center') and not coordinates:
            center = element['center']
            geometry = {'type':'Point', 'coordinates':[center['lon'],center['lat']]}
            representation = 'center_only'
        else:
            rejected.append({'facility_id':fid, 'reason':'MISSING_OR_UNASSEMBLED_GEOMETRY'})
            continue
        features.append({'type':'Feature', 'id':fid, 'geometry':geometry,
            'properties':{'facility_id':fid, 'facility_type':category, 'category':category,
                          'tags':tags, 'geometry_representation':representation}})
    return {'type':'FeatureCollection', 'features':features}, {
        'input_features':len(document['elements']), 'accepted_features':len(features),
        'rejected_features':rejected, 'osm_base_timestamp':document.get('osm3s',{}).get('timestamp_osm_base')}
