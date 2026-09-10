# Dataset inputs and provenance

No production training dataset or reviewed labels exist in this phase.
`data/samples/firms_nasa_tutorial.csv` is a five-row published NASA example; its
source/date and limitations are recorded alongside it. Generated Parquet/raw data
are ignored by Git. The real event dataset requires much broader observations.

## FIRMS input

Required: `latitude`, `longitude`, and either `acquisition_time` or both `acq_date`
and `acq_time`. Optional canonical thermal fields: `frp`, `brightness` (VIIRS
`bright_ti4` alias); missing values remain null. Preserve `satellite`, `instrument`,
`daynight`, confidence, scan, track, source versions and extra input columns.
Validation report and rejection CSV account for rejected and duplicate rows.
For live ingestion, legacy ORM thermal fields must be present; otherwise the API
reports an explicit rejection. VIIRS categorical confidence is retained as native
provider data; the legacy numeric confidence receives 0 (unknown), not an invented
probability. The new offline dataset preserves the native value without conversion.

Live FIRMS fetch now uses the documented area endpoint structure and server-side
key. Its current sensor is NOAA-20 NRT; use offline CSV exports for multiple sensors
or larger historical datasets. `FIRMS_API_KEY` and its `FIRMS_MAP_KEY` alias are supported.

## Reference GeoJSON

Supply a FeatureCollection with `properties.category` (or `infra_type`):

- Point: refinery, factory, power_plant, mine, industrial_area, settlement.
- Polygon/MultiPolygon: forest, agriculture, urban, industrial; typed facility
  categories also accepted as footprints.
- LineString/MultiLineString: road, railway, pipeline (legacy context only).

Use stable OSM identifiers such as `way/123` or `node/123` in feature `id` and
explicit source/version information in `--reference-source`. Standard Overpass
responses must be converted to this schema; centers are not footprints. A CRS
other than EPSG:4326 must be passed explicitly with `--reference-crs`.

Optional top-level `available_categories` declares loaded categories, including
empty surveyed layers. Optional top-level `coverage` maps categories to polygon
geometries in the same input CRS. Fractions are computed only inside that declared
coverage. An empty feature array without declared categories means unavailable.

Example schema only (coordinates are artificial, not an actual OSM export):

```json
{
  "type": "FeatureCollection",
  "available_categories": ["factory"],
  "features": [{
    "type": "Feature",
    "id": "example-facility",
    "properties": {"category": "factory", "name": "Synthetic schema example"},
    "geometry": {"type": "Point", "coordinates": [70, 22]}
  }]
}
```

The existing `data/landcover.geojson`, `data/network.geojson` and seeded assets are
demonstration layers. The builder deliberately does not assume that they are real
OSM or measured land cover. No missing facility, raster fraction or imagery field
is fabricated. OSM completeness and observation coverage require independent review.

## Dataset inspection

Read the `.manifest.json` first; inspect null counts, provenance and configuration.
Read `.membership.parquet` to trace event aggregation. The `.schema.json` identifies
all nullable features and units. Identifiers, source strings and evidence JSON are
audit context, not automatic model inputs. Avoid target leakage when selecting
training features in later phases.

The sample output has 3 events from 5 observations, no earlier observations and
no reference layers. All spatial context is null; historical FRP baselines are
null; persistence is zero. These are correct unavailable-data results, not evidence
that the sites lack industry or persistent heat.

## India readiness extension

See [INDIA_DATA_READINESS.md](INDIA_DATA_READINESS.md) for multi-file India
preprocessing, separately sourced industrial/land-cover bundles and exact report
commands. Preprocessing now preserves per-file lineage and dates/bounds/sensor/hash
metadata. Outside declared reference coverage, negative polygon overlap is unknown
(null). Industrial land-cover polygons cannot establish facility identity/counts.
The existing tutorial is retained only as a plumbing fixture; no India dataset has
been substituted or fabricated.
