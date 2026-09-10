"""Demo and local-vector land cover; remote raster ingestion is future work."""
from __future__ import annotations

from app.providers.osm import load_landcover_geojson
from app.config import settings


class LandCoverProvider:
    name = "base"
    mode = "unknown"

    def fetch(self) -> dict:
        raise NotImplementedError


class SeededLandCoverProvider(LandCoverProvider):
    name = "Land Cover"
    mode = "demo"

    def fetch(self) -> dict:
        return load_landcover_geojson()


class UnavailableLandCoverProvider(LandCoverProvider):
    name = "Land Cover"
    mode = "unavailable"

    def fetch(self) -> dict:
        from app.providers.firms import ProviderUnavailable

        raise ProviderUnavailable("Live land-cover API not configured for this deployment")


def get_landcover_provider() -> LandCoverProvider:
    if settings.DEMO_MODE and not settings.SATELLITE_API_KEY:
        return SeededLandCoverProvider()
    return UnavailableLandCoverProvider()

class FileLandCoverProvider(LandCoverProvider):
    """Explicit user-supplied vector export; no seeded fallback or raster claims."""
    name = 'Local land-cover export'
    mode = 'file'

    def __init__(self, path):
        from pathlib import Path
        self.path = Path(path)

    def fetch(self) -> dict:
        import json
        document = json.loads(self.path.read_text())
        if document.get('type') != 'FeatureCollection':
            raise ValueError('Land cover must be a GeoJSON FeatureCollection')
        return document
