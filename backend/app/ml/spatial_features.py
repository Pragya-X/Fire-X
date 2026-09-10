"""Nullable event context from explicitly supplied reference layers.

Counts describe observed assets, never OSM completeness. Fractions require a
supplied coverage polygon covering the whole 1 km buffer, otherwise remain null.
"""
from __future__ import annotations
import json
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform, unary_union
from app.gis.engine import SpatialDataset, validate_coordinates, local_transformer, _equirect_km

INDUSTRIAL = ('refinery','factory','power_plant','mine','industrial_area','oil_gas')
SPATIAL_FIELDS = ['dist_nearest_industrial_km','dist_refinery_km','dist_factory_km','dist_powerplant_km','dist_mine_km',
    'industrial_count_500m','industrial_count_1km','industrial_count_5km','inside_industrial_polygon',
    'nearest_facility_id','nearest_facility_type','dist_forest_km','dist_agriculture_km','dist_settlement_km',
    'inside_forest','inside_agriculture','inside_urban','forest_fraction_1km','agriculture_fraction_1km','industrial_fraction_1km']


def event_spatial_features(dataset: SpatialDataset | None, lat: float, lon: float) -> dict:
    validate_coordinates(lat, lon)
    result = dict.fromkeys(SPATIAL_FIELDS)
    if dataset is None:
        return result
    candidates = []
    for cat in INDUSTRIAL:
        found = dataset.nearest_point(cat,lat,lon)
        footprints = [f for f in dataset.geometries('industrial') if f.meta.get('facility_type') == cat]
        for footprint in footprints:
            distance = _equirect_km(lat,Point(lon,lat),footprint.geom)
            if found is None or distance < found['distance_km']:
                found = {'distance_km':distance,'id':footprint.id}
        key = 'dist_powerplant_km' if cat=='power_plant' else f'dist_{cat}_km'
        if key in result:
            result[key] = found['distance_km'] if found else None
        if found:
            candidates.append((found['distance_km'],found['id'],cat))
    industrial_polygon = dataset.nearest_geometry('industrial',lat,lon)
    # Land-cover cells provide industrial context, not verified facility identity.
    for polygon in dataset.geometries('industrial'):
        if polygon.meta.get('reference_role') != 'landcover':
            candidates.append((_equirect_km(lat,Point(lon,lat),polygon.geom),polygon.id,
                               polygon.meta.get('facility_type','industrial_area')))
    if candidates:
        distance, fid, kind = min(candidates)
        result.update(dist_nearest_industrial_km=distance,nearest_facility_id=fid,nearest_facility_type=kind)
    if industrial_polygon:
        result['dist_nearest_industrial_km'] = min(result['dist_nearest_industrial_km'],industrial_polygon['distance_km']) if candidates else industrial_polygon['distance_km']
    facility_layer_available = bool(set(INDUSTRIAL).intersection(dataset.available_categories)) or any(
        f.meta.get('reference_role') != 'landcover' for f in dataset.geometries('industrial'))
    if facility_layer_available:
        for radius, suffix in ((.5,'500m'),(1,'1km'),(5,'5km')):
            ids = {f.id for cat in INDUSTRIAL for f in dataset.points_within(cat,lat,lon,radius)}
            ids.update(f.id for f in dataset.geometries('industrial') if f.meta.get('reference_role') != 'landcover' and _equirect_km(lat,Point(lon,lat),f.geom)<=radius)
            result[f'industrial_count_{suffix}'] = len(ids)
    for cat in ('forest','agriculture','settlement'):
        found = dataset.nearest_point(cat,lat,lon) if cat=='settlement' else dataset.nearest_geometry(cat,lat,lon)
        result[f'dist_{cat}_km'] = found['distance_km'] if found else None
    project = local_transformer(lat,lon).transform
    buffer = Point(0,0).buffer(1000,resolution=64)
    for cat in ('forest','agriculture','urban','industrial'):
        features = dataset.geometries(cat)
        key = 'inside_industrial_polygon' if cat=='industrial' else f'inside_{cat}'
        coverage = dataset.coverage.get(cat)
        if cat in dataset.available_categories:
            inside = any(f.geom.covers(Point(lon,lat)) for f in features)
            result[key] = True if inside else (False if coverage is not None and coverage.covers(Point(lon,lat)) else None)
        if cat != 'urban' and coverage is not None and transform(project,coverage).covers(buffer):
            polygons = [transform(project,f.geom) for f in features if f.geom.geom_type in ('Polygon','MultiPolygon')]
            result[f'{cat}_fraction_1km'] = min(1.0,unary_union(polygons).intersection(buffer).area/buffer.area) if polygons else 0.0
    return result


def load_reference_geojson(path: Path, *, source: str, crs: str = 'EPSG:4326') -> SpatialDataset:
    """Import explicit category/infra_type GeoJSON; no seeded data is auto-loaded.

    Optional top-level `available_categories` includes empty surveyed layers;
    `coverage` maps categories to geometries in the input CRS. Source is required.
    """
    return load_reference_document(json.loads(path.read_text()), source=source, crs=crs, path=str(path))


def load_reference_document(document: dict, *, source: str, crs: str = 'EPSG:4326', path: str = '') -> SpatialDataset:
    if document.get('type') != 'FeatureCollection' or not source.strip():
        raise ValueError('Expected FeatureCollection and nonempty source provenance')
    dataset = SpatialDataset()
    project = Transformer.from_crs(crs,'EPSG:4326',always_xy=True).transform
    allowed = set(dataset.POINT_CATEGORIES) | set(dataset.GEOMETRY_CATEGORIES)
    for cat in document.get('available_categories',[]):
        if cat not in allowed: raise ValueError(f'Unknown category {cat}')
        dataset.available_categories.add(cat)
    for i, feature in enumerate(document.get('features',[])):
        properties = feature.get('properties') or {}
        cat = properties.get('category',properties.get('infra_type',properties.get('facility_type')))
        if cat not in allowed: raise ValueError(f'Feature {i}: missing/unknown category')
        geometry = transform(project,shape(feature['geometry']))
        if cat in ('forest','agriculture','urban','industrial','water','administrative') and geometry.geom_type not in ('Polygon','MultiPolygon'):
            raise ValueError(f'Category {cat} requires polygons')
        if geometry.is_empty or not geometry.is_valid:
            raise ValueError(f'Invalid geometry at feature {i}')
        if cat in ('road','railway','pipeline') and geometry.geom_type not in ('LineString','MultiLineString'):
            raise ValueError(f'Category {cat} requires line geometry')
        minx,miny,maxx,maxy = geometry.bounds
        validate_coordinates(miny,minx); validate_coordinates(maxy,maxx)
        fid = str(feature.get('id',properties.get('facility_id',properties.get('id',f'feature-{i}'))))
        name = str(properties.get('name',fid))
        if geometry.geom_type == 'Point' and cat in dataset.POINT_CATEGORIES:
            dataset.add_point(cat,fid,name,geometry.y,geometry.x,properties)
        elif geometry.geom_type in ('Polygon','MultiPolygon') and cat in INDUSTRIAL:
            dataset.add_geometry('industrial',fid,name,geometry,{**properties,'facility_type':cat})
            # Facility-type distances use its representative point; industrial
            # distance/overlap uses the actual footprint.
            point=geometry.representative_point()
            dataset.add_point(cat,fid,name,point.y,point.x,properties)
        elif cat in dataset.GEOMETRY_CATEGORIES:
            dataset.add_geometry(cat,fid,name,geometry,properties)
        else:
            raise ValueError(f'Unsupported geometry/category at feature {i}')
    for cat, geom in document.get('coverage',{}).items():
        if cat not in allowed: raise ValueError(f'Unknown coverage category {cat}')
        coverage = transform(project,shape(geom))
        if coverage.is_empty or not coverage.is_valid or coverage.geom_type not in ('Polygon','MultiPolygon'):
            raise ValueError(f'Invalid polygon coverage for {cat}')
        minx,miny,maxx,maxy = coverage.bounds
        validate_coordinates(miny,minx); validate_coordinates(maxy,maxx)
        if cat not in dataset.available_categories:
            raise ValueError(f'Coverage declared for an unavailable category: {cat}')
        dataset.coverage[cat] = coverage
    dataset.provenance = {'source':source,'path':str(path),'input_crs':crs}
    dataset.build_indexes()
    return dataset
