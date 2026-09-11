"""Satellite validation provider.

Live providers (Sentinel-2 / Landsat) require credentials. The demo provider
produces deterministic validation metadata from the hotspot's own signature and
clearly labels itself as a demo layer - it never claims to be live imagery.
"""
from __future__ import annotations

import random
from typing import Optional

from app.config import settings
from app.models import Hotspot


class SatelliteProvider:
    name = "Satellite"
    mode = "unknown"

    def validate(self, hotspot: Hotspot) -> dict:
        raise NotImplementedError


class DemoSatelliteProvider(SatelliteProvider):
    name = "Satellite Validation"
    mode = "demo"

    def validate(self, hotspot: Hotspot) -> dict:
        rng = random.Random(hotspot.id * 31 + int(hotspot.frp * 100))
        is_veg = hotspot.classification in ("Wildfire", "Agricultural Burning")
        smoke = hotspot.classification in ("Wildfire", "Industrial Fire") and rng.random() < 0.7
        status = rng.choices(
            ["CONFIRMED", "LIKELY", "UNCERTAIN", "NOT VALIDATED"],
            weights=[35, 35, 20, 10] if is_veg else [20, 30, 25, 25],
        )[0]
        return {
            "status": status,
            "provider": "demo",
            "smoke_indication": smoke,
            "burn_area_ha": round(max(0.5, hotspot.frp * rng.uniform(1.0, 2.2)), 1),
            "fire_extent_km2": round(max(0.01, hotspot.frp * 0.02), 3),
            "ndvi_before": round(rng.uniform(0.2, 0.55), 3),
            "ndvi_after": round(max(-0.2, rng.uniform(-0.1, 0.35)), 3),
            "notes": "Demo satellite layer - synthetic validation based on thermal signature.",
        }


class LiveSatelliteProvider(SatelliteProvider):
    """Real Planet Data API integration for satellite validation."""

    name = "Planet Insights"
    mode = "live"

    def validate(self, hotspot: Hotspot) -> dict:
        import httpx
        from datetime import timedelta
        
        # Create a tiny bounding box around the hotspot
        lat, lon = hotspot.latitude, hotspot.longitude
        delta = 0.01  # approx 1km
        geometry = {
            "type": "Polygon",
            "coordinates": [
                [
                    [lon - delta, lat - delta],
                    [lon + delta, lat - delta],
                    [lon + delta, lat + delta],
                    [lon - delta, lat + delta],
                    [lon - delta, lat - delta],
                ]
            ],
        }

        # Search last 2 days only for faster query (instead of 5 before + 1 after = 6 days)
        start_time = (hotspot.acquisition_time - timedelta(days=1)).isoformat()
        if not start_time.endswith("Z") and "+" not in start_time:
            start_time += "Z"
            
        end_time = (hotspot.acquisition_time + timedelta(days=1)).isoformat()
        if not end_time.endswith("Z") and "+" not in end_time:
            end_time += "Z"

        search_payload = {
            "item_types": ["PSScene"],
            "filter": {
                "type": "AndFilter",
                "config": [
                    {
                        "type": "GeometryFilter",
                        "field_name": "geometry",
                        "config": geometry,
                    },
                    {
                        "type": "DateRangeFilter",
                        "field_name": "acquired",
                        "config": {"gte": start_time, "lte": end_time},
                    },
                    {
                        "type": "RangeFilter",
                        "field_name": "cloud_cover",
                        "config": {"lte": 0.2},
                    },
                ],
            },
        }

        try:
            # We use a synchronous httpx request for simplicity in the provider architecture.
            with httpx.Client() as client:
                resp = client.post(
                    "https://api.planet.com/data/v1/quick-search",
                    json=search_payload,
                    auth=(settings.SATELLITE_API_KEY, ""),
                    timeout=3.0  # faster timeout for quick response
                )
            
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            
            item = features[0] if features else None
            return {
                "status": "NOT VALIDATED",
                "provider": "planet",
                "smoke_indication": None,
                "burn_area_ha": None,
                "fire_extent_km2": None,
                "ndvi_before": None,
                "ndvi_after": None,
                "notes": (
                    f"Imagery candidate {item.get('id', '')} acquired "
                    f"{item.get('properties', {}).get('acquired', '')}. "
                    "Catalog metadata only; pixels have not been analyzed. Fire, smoke, burn area and NDVI remain unverified."
                    if item else "No cloud-free Planet imagery found in the search window."
                ),
            }

        except Exception as e:
            from app.providers.firms import ProviderUnavailable
            raise ProviderUnavailable("Planet imagery search unavailable; no validation produced") from e


class UnavailableSatelliteProvider(SatelliteProvider):
    name = "Satellite imagery unavailable"
    mode = "unavailable"

    def validate(self, hotspot: Hotspot) -> dict:
        from app.providers.firms import ProviderUnavailable
        raise ProviderUnavailable("Satellite imagery credentials are not configured")


def get_satellite_provider() -> SatelliteProvider:
    if settings.SATELLITE_API_KEY:
        return LiveSatelliteProvider()
    if settings.DEMO_MODE:
        return DemoSatelliteProvider()
    return UnavailableSatelliteProvider()
