import json
import pytest
from shapely.geometry import Polygon, box, mapping
from pyproj import Transformer
from app.gis.engine import SpatialDataset, haversine_km
from app.ml.spatial_features import event_spatial_features, load_reference_geojson


def test_high_latitude_nearest_uses_metric():
    ds=SpatialDataset()
    ds.add_point('factory','east','east',80,1)
    ds.add_point('factory','north','north',80.5,0)
    ds.build_indexes()
    assert ds.nearest_point('factory',80,0)['id']=='east'


def test_missing_boundary_holes_and_fractions():
    assert event_spatial_features(None,0,0)['industrial_count_1km'] is None
    ds=SpatialDataset()
    polygon=Polygon([(-.1,-.1),(.1,-.1),(.1,.1),(-.1,.1)],holes=[[(-.01,-.01),(.01,-.01),(.01,.01),(-.01,.01)]])
    ds.add_geometry('forest','f','f',polygon)
    ds.coverage['forest']=box(-1,-1,1,1)
    r=event_spatial_features(ds,0,0)
    assert r['inside_forest'] is False and r['dist_forest_km']>1
    assert r['forest_fraction_1km']==0
    assert event_spatial_features(ds,.1,0)['inside_forest'] is True
    with pytest.raises(ValueError): event_spatial_features(ds,91,0)


def test_crs_import_and_counts(tmp_path):
    x,y=Transformer.from_crs(4326,3857,always_xy=True).transform(70,22)
    path=tmp_path/'ref.json'
    path.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','id':'osm/node/1','properties':{'category':'factory'},'geometry':{'type':'Point','coordinates':[x,y]}}]}))
    ds=load_reference_geojson(path,source='synthetic-test',crs='EPSG:3857')
    r=event_spatial_features(ds,22,70)
    assert r['dist_factory_km']<.001 and r['industrial_count_500m']==1
    assert r['inside_industrial_polygon'] is None
    assert r['industrial_fraction_1km'] is None


def test_polygon_facility_distance_uses_footprint(tmp_path):
    path=tmp_path/'ref.json'
    path.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','id':'osm/way/1','properties':{'category':'factory'},'geometry':mapping(box(0,0,.1,.1))}]}))
    ds=load_reference_geojson(path,source='synthetic-test')
    result=event_spatial_features(ds,.01,.01)
    assert result['inside_industrial_polygon'] is True
    assert result['dist_factory_km']==0
    assert result['industrial_count_500m']==1
