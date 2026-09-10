# Supply real reference files here

No industrial or land-cover geometry is bundled as representative India data.

Expected user-supplied files:

- `industrial.geojson`: sourced facilities/areas with stable feature `id` or
  `properties.facility_id`, explicit category/facility type and true geometry.
- `landcover.geojson`: sourced forest/agriculture/urban/industrial polygons with
  stable feature IDs and an explicit category mapping.

Copy `../reference_bundle.example.json` to `../reference_bundle.json`, replace
its provenance placeholders and set the **actual input CRS** for each file.
Paths in that JSON resolve relative to the bundle. Geometry and metadata schemas,
Overpass conversion and observation-coverage requirements are documented in
`docs/INDIA_DATA_READINESS.md` at the repository root.

Supply actual surveyed/valid-data coverage polygons inside the FeatureCollection
`coverage` mapping if area fractions are needed. Do not substitute the bounding
box of observed features for known coverage. Missing values remain unavailable.
