-- Run after application table creation, as an explicit migration with backup.
-- Generated geometries cannot become stale when latitude/longitude/WKT changes.
BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis;
ALTER TABLE thermal_events ADD COLUMN IF NOT EXISTS geom geometry(Point,4326)
  GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude,latitude),4326)) STORED;
ALTER TABLE thermal_observations ADD COLUMN IF NOT EXISTS geom geometry(Point,4326)
  GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude,latitude),4326)) STORED;
ALTER TABLE reference_facilities ADD COLUMN IF NOT EXISTS geom geometry(Geometry,4326)
  GENERATED ALWAYS AS (ST_GeomFromText(geometry_wkt,4326)) STORED;
CREATE INDEX IF NOT EXISTS thermal_events_geom_gist ON thermal_events USING GIST (geom);
CREATE INDEX IF NOT EXISTS thermal_observations_geom_gist ON thermal_observations USING GIST (geom);
CREATE INDEX IF NOT EXISTS reference_facilities_geom_gist ON reference_facilities USING GIST (geom);
CREATE INDEX IF NOT EXISTS event_predictions_event_time ON event_predictions(event_id,created_at);
COMMIT;
