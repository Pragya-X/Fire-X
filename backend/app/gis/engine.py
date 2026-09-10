"""EPSG:4326 context; haversine points and local azimuthal-equidistant geometry distances."""
from __future__ import annotations

import math
import random
from functools import lru_cache
from pyproj import CRS, Transformer
from shapely.ops import transform
from typing import Any, Optional

from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

KM_PER_DEG = 111.32


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def validate_coordinates(lat: float, lon: float) -> None:
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("Invalid WGS84 latitude/longitude")


@lru_cache(maxsize=2048)
def local_transformer(lat: float, lon: float) -> Transformer:
    validate_coordinates(lat, lon)
    return Transformer.from_crs("EPSG:4326", CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"), always_xy=True)


def _equirect_km(lat0: float, geom_a: Any, geom_b: Any) -> float:
    """Compatibility name; now uses local metric AEQD preserving holes/multipart.

    Intended for local context geometries; very large/antipodal polygons must be
    clipped upstream. Straight projected edges approximate geodesic boundaries.
    """
    project = local_transformer(lat0, geom_a.x).transform
    return transform(project, geom_a).distance(transform(project, geom_b)) / 1000


class Feature:
    """A point feature (asset, settlement)."""

    def __init__(self, fid: str, name: str, lat: float, lon: float, meta: Optional[dict] = None):
        self.id = fid
        self.name = name
        self.lat = lat
        self.lon = lon
        self.point = Point(lon, lat)
        self.meta = meta or {}


class GeometryFeature:
    """A line/polygon feature (road, railway, pipeline, forest, agriculture)."""

    def __init__(self, fid: str, name: str, geom: Any, meta: Optional[dict] = None):
        self.id = fid
        self.name = name
        self.geom = geom
        self.meta = meta or {}


class SpatialDataset:
    """Holds all spatial reference layers with per-category spatial indexes."""

    POINT_CATEGORIES = (
        "refinery",
        "factory",
        "power_plant",
        "mine",
        "settlement",
        "industrial_area",
        "oil_gas",
    )
    GEOMETRY_CATEGORIES = ("forest", "agriculture", "road", "railway", "pipeline", "industrial", "urban", "water", "administrative")

    def __init__(self) -> None:
        self.available_categories: set[str] = set()
        self.coverage: dict[str, Any] = {}
        self.provenance: dict[str, Any] = {}
        self._points: dict[str, list[Feature]] = {c: [] for c in self.POINT_CATEGORIES}
        self._geoms: dict[str, list[GeometryFeature]] = {c: [] for c in self.GEOMETRY_CATEGORIES}
        self._point_trees: dict[str, Optional[STRtree]] = {c: None for c in self.POINT_CATEGORIES}
        self._geom_trees: dict[str, Optional[STRtree]] = {c: None for c in self.GEOMETRY_CATEGORIES}

    # ---------- builders ----------
    def add_point(self, category: str, fid: str, name: str, lat: float, lon: float, meta: Optional[dict] = None) -> None:
        if category not in self._points:
            raise KeyError(f"unknown point category {category}")
        validate_coordinates(lat, lon)
        self.available_categories.add(category)
        self._points[category].append(Feature(fid, name, lat, lon, meta))

    def add_geometry(self, category: str, fid: str, name: str, geom: Any, meta: Optional[dict] = None) -> None:
        if category not in self._geoms:
            raise KeyError(f"unknown geometry category {category}")
        if geom.is_empty or not geom.is_valid:
            raise ValueError("Invalid/empty reference geometry")
        self.available_categories.add(category)
        self._geoms[category].append(GeometryFeature(fid, name, geom, meta))

    def build_indexes(self) -> None:
        for cat, feats in self._points.items():
            if feats:
                self._point_trees[cat] = STRtree([f.point for f in feats])
        for cat, feats in self._geoms.items():
            if feats:
                self._geom_trees[cat] = STRtree([f.geom for f in feats])

    # ---------- queries ----------
    def nearest_point(self, category: str, lat: float, lon: float) -> Optional[dict]:
        validate_coordinates(lat, lon)
        feats = self._points.get(category) or []
        if not feats:
            return None
        f = min(feats, key=lambda x: haversine_km(lat, lon, x.lat, x.lon))
        return {
            "distance_km": round(haversine_km(lat, lon, f.lat, f.lon), 3),
            "id": f.id,
            "name": f.name,
            "meta": f.meta,
        }

    def nearest_geometry(self, category: str, lat: float, lon: float) -> Optional[dict]:
        validate_coordinates(lat, lon)
        feats = self._geoms.get(category) or []
        if not feats:
            return None
        q = Point(lon, lat)
        f = min(feats, key=lambda x: _equirect_km(lat, q, x.geom))
        return {
            "distance_km": round(_equirect_km(lat, q, f.geom), 3),
            "id": f.id,
            "name": f.name,
            "meta": f.meta,
        }

    def points(self, category: str) -> list[Feature]:
        return list(self._points.get(category, []))

    def geometries(self, category: str) -> list[GeometryFeature]:
        return list(self._geoms.get(category, []))

    def points_within(self, category: str, lat: float, lon: float, radius_km: float) -> list[Feature]:
        return [f for f in self._points.get(category, []) if haversine_km(lat, lon, f.lat, f.lon) <= radius_km]

    def containing_polygon(self, category: str, lat: float, lon: float) -> Optional[GeometryFeature]:
        q = Point(lon, lat)
        for f in self._geoms.get(category, []):
            if f.geom.covers(q):
                return f
        return None

    # ---------- aggregate ----------
    def full_context(self, lat: float, lon: float) -> dict:
        ctx: dict = {}
        for cat in self.POINT_CATEGORIES:
            nearest = self.nearest_point(cat, lat, lon)
            ctx[cat] = nearest or {"distance_km": -1.0, "id": "", "name": ""}
        for cat in self.GEOMETRY_CATEGORIES:
            nearest = self.nearest_geometry(cat, lat, lon)
            ctx[cat] = nearest or {"distance_km": -1.0, "id": "", "name": ""}
        return ctx

    def land_cover(self, lat: float, lon: float, rng: Optional[random.Random] = None) -> str:
        for cat in ("refinery", "factory", "power_plant", "mine", "industrial_area"):
            nearest = self.nearest_point(cat, lat, lon)
            if nearest and nearest["distance_km"] <= 3.0:
                return "Industrial"
        if self.containing_polygon("forest", lat, lon):
            return "Forest"
        if self.containing_polygon("agriculture", lat, lon):
            return "Agriculture"
        nearest_settlement = self.nearest_point("settlement", lat, lon)
        if nearest_settlement and nearest_settlement["distance_km"] <= 5.0:
            return "Urban"
        return "Other"


def compute_infrastructure_features(dataset: SpatialDataset, lat: float, lon: float) -> dict:
    """Distance (km) to the nearest feature of each category. -1.0 when a layer is absent."""
    ctx = dataset.full_context(lat, lon)
    out = {
        "nearest_refinery_distance": ctx["refinery"]["distance_km"],
        "nearest_factory_distance": ctx["factory"]["distance_km"],
        "nearest_powerplant_distance": ctx["power_plant"]["distance_km"],
        "nearest_mine_distance": ctx["mine"]["distance_km"],
        "nearest_forest_distance": ctx["forest"]["distance_km"],
        "nearest_agriculture_distance": ctx["agriculture"]["distance_km"],
        "nearest_settlement_distance": ctx["settlement"]["distance_km"],
        "nearest_road_distance": ctx["road"]["distance_km"],
        "nearest_railway_distance": ctx["railway"]["distance_km"],
        "nearest_pipeline_distance": ctx["pipeline"]["distance_km"],
        "nearest_refinery_id": ctx["refinery"]["id"],
        "nearest_factory_id": ctx["factory"]["id"],
        "nearest_powerplant_id": ctx["power_plant"]["id"],
        "nearest_mine_id": ctx["mine"]["id"],
        "nearest_forest_id": ctx["forest"]["id"],
        "nearest_agriculture_id": ctx["agriculture"]["id"],
        "nearest_settlement_id": ctx["settlement"]["id"],
    }
    return out


def wkt_point(lat: float, lon: float) -> str:
    return f"POINT({lon} {lat})"


def geojson_points(items: list[dict], props: tuple[str, ...]) -> dict:
    features = []
    for it in items:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [it["longitude"], it["latitude"]]},
                "properties": {k: it.get(k) for k in props},
            }
        )
    return {"type": "FeatureCollection", "features": features}