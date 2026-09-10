"""Versioned industrial/land-cover files merged into the existing SpatialDataset."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from shapely.ops import unary_union
from shapely.errors import ShapelyError
from pyproj.exceptions import ProjError
from app.gis.engine import SpatialDataset
from app.ml.spatial_features import INDUSTRIAL, load_reference_document
from app.providers.landcover import FileLandCoverProvider
from app.providers.osm import reference_features


class ReferenceBundleError(ValueError):
    def __init__(self, message: str, report: dict):
        super().__init__(message)
        self.report = report


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_reference_bundle(path: Path) -> tuple[SpatialDataset, dict]:
    document = json.loads(path.read_text())
    if document.get('version') != 1 or not isinstance(document.get('layers'), list) or not document['layers']:
        raise ValueError('Reference bundle requires version=1 and nonempty layers')
    combined = SpatialDataset()
    layers, seen = [], set()
    for entry in document['layers']:
        name, role = entry.get('name'), entry.get('role')
        if not name or name in seen or role not in ('industrial','landcover','administrative','transport','water'):
            raise ValueError('Layers require unique names and a supported reference role')
        seen.add(name)
        for required in ('path','source','version','crs'):
            if entry.get(required) is None or not str(entry.get(required,'')).strip():
                raise ValueError(f'Layer {name} missing {required}')
        layer_path = (path.parent / entry['path']).resolve()
        format_name = entry.get('format','geojson')
        if format_name not in ('geojson','overpass-json'):
            raise ValueError(f'Unsupported reference format {format_name}')
        source_crs = entry['crs']
        if format_name == 'overpass-json':
            if role != 'industrial' or source_crs != 'EPSG:4326':
                raise ValueError('Overpass industrial exports require EPSG:4326')
            raw, conversion = reference_features(json.loads(layer_path.read_text()))
        else:
            raw = FileLandCoverProvider(layer_path).fetch() if role=='landcover' else json.loads(layer_path.read_text())
            conversion = {'input_features':len(raw.get('features',[])), 'rejected_features':[]}
        raw = copy.deepcopy(raw)
        rejected = list(conversion.get('rejected_features',[]))
        excluded, accepted, identifiers = [], [], set()
        category_property = entry.get('category_property','category')
        category_map = entry.get('category_map',{})
        for index, feature in enumerate(raw.get('features',[])):
            properties = feature.get('properties') or {}
            identity = feature.get('id',properties.get('facility_id',properties.get('id')))
            raw_category = properties.get(category_property, properties.get('facility_type',properties.get('infra_type')))
            category = category_map.get(str(raw_category),raw_category)
            if str(raw_category) in category_map and category is None:
                excluded.append({'feature_id':identity, 'reason':'EXPLICIT_OUT_OF_SCOPE_MAPPING', 'source_category':raw_category})
                continue
            allowed = {'industrial':set(INDUSTRIAL) | {'industrial','settlement'},
                'landcover':{'forest','agriculture','urban','industrial','water'},
                'administrative':{'administrative'},'transport':{'road','railway','pipeline'},'water':{'water'}}[role]
            reason = None
            if identity is None or not str(identity).strip(): reason = 'MISSING_STABLE_FEATURE_ID'
            elif str(identity) in identifiers: reason = 'DUPLICATE_FEATURE_ID'
            elif category not in allowed: reason = 'UNKNOWN_OR_WRONG_ROLE_CATEGORY'
            if reason:
                rejected.append({'feature_id':identity,'index':index,'reason':reason,'source_category':raw_category})
                continue
            identifiers.add(str(identity))
            feature['id'] = str(identity)
            feature['properties'] = {**properties, 'category':category, 'source':entry['source'],
                'source_version':entry['version'], 'reference_layer':name, 'reference_role':role,
                'facility_id':str(identity) if role=='industrial' else properties.get('facility_id')}
            accepted.append(feature)
        raw['features'] = accepted
        layer_report = {'name':name, 'role':role, 'path':str(layer_path), 'source':entry['source'],
            'version':entry['version'], 'input_crs':source_crs, 'sha256':sha256(layer_path),
            'input_features':conversion['input_features'], 'accepted_features':len(accepted),
            'rejected_features':rejected, 'excluded_features':excluded,
            'osm_base_timestamp':conversion.get('osm_base_timestamp')}
        layers.append(layer_report)
        if rejected:
            raise ReferenceBundleError(f'Invalid features in layer {name}; see reference validation report', {'layers':layers})
        try:
            loaded = load_reference_document(raw,source=entry['source'],crs=source_crs,path=str(layer_path))
        except (ValueError, TypeError, KeyError, ShapelyError, ProjError) as exc:
            layer_report['geometry_error'] = str(exc)
            raise ReferenceBundleError(f'Invalid geometry/schema in {name}', {'layers':layers}) from exc
        layer_report['categories'] = sorted(loaded.available_categories)
        layer_report['coverage_categories'] = sorted(loaded.coverage)
        layer_report['center_only_features'] = sum(f['properties'].get('geometry_representation')=='center_only' for f in accepted)
        for cat in loaded.POINT_CATEGORIES:
            existing = {f.id for f in combined.points(cat)}
            for feature in loaded.points(cat):
                if feature.id in existing:
                    raise ReferenceBundleError(f'Duplicate facility identity across layers: {feature.id}', {'layers':layers})
                combined.add_point(cat,feature.id,feature.name,feature.lat,feature.lon,feature.meta)
        for cat in loaded.GEOMETRY_CATEGORIES:
            existing = {f.id for f in combined.geometries(cat)}
            for feature in loaded.geometries(cat):
                if feature.id in existing:
                    raise ReferenceBundleError(f'Duplicate geometry identity across layers: {feature.id}', {'layers':layers})
                combined.add_geometry(cat,feature.id,feature.name,feature.geom,feature.meta)
        combined.available_categories.update(loaded.available_categories)
        for cat, geometry in loaded.coverage.items():
            combined.coverage[cat] = unary_union([combined.coverage[cat],geometry]) if cat in combined.coverage else geometry
    config_hash = sha256(path)
    digest = hashlib.sha256(json.dumps({'config_sha256':config_hash,
        'layers':[{k:layer[k] for k in ('name','sha256')} for layer in layers]},sort_keys=True).encode()).hexdigest()
    provenance = {'reference_source':' | '.join(layer['source'] for layer in layers),
        'reference_sha256':digest, 'reference_crs':'EPSG:4326', 'reference_config_sha256':config_hash,
        'reference_bundle_path':str(path.resolve()), 'layers':layers}
    for role,prefix in (('industrial','industrial_reference'),('landcover','landcover')):
        selected = [layer for layer in layers if layer['role']==role]
        provenance[f'{prefix}_source'] = ' | '.join(layer['source'] for layer in selected) or None
        provenance[f'{prefix}_version'] = ' | '.join(str(layer['version']) for layer in selected) or None
    combined.provenance = {'source':provenance['reference_source'], **provenance}
    combined.build_indexes()
    return combined, provenance
