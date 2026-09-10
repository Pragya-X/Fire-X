"""NASA FIRMS data integration.

Provider interface: ``FireDataProvider.fetch(...)`` returns FIRMS-like records:

    {"latitude", "longitude", "acq_time" (ISO), "brightness", "frp",
     "confidence", "satellite", "daynight", "external_id"}

- ``FirmsProvider`` talks to the real NASA FIRMS CSV endpoint when
  ``FIRMS_API_KEY`` is configured (server-side only - keys never reach the
  frontend).
- ``DemoFireDataProvider`` generates deterministic FIRMS-like detections when
  no key is present, so the platform is always demonstrable.
"""
from __future__ import annotations

import csv
import io
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.config import settings
from app.seed_data import INDUSTRIAL_ZONES


class ProviderUnavailable(Exception):
    pass


class FireDataProvider:
    name = "base"
    mode = "unknown"

    def fetch(self, area: str = "India", from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> list[dict]:
        raise NotImplementedError


class FirmsProvider(FireDataProvider):
    name = "NASA FIRMS"
    mode = "live"

    def fetch(self, area: str = "India", from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> list[dict]:
        key = settings.firms_api_key
        if not key:
            raise ProviderUnavailable("FIRMS_API_KEY not configured")
        from_date = from_date or datetime.now(timezone.utc) - timedelta(days=2)
        to_date = to_date or datetime.now(timezone.utc)
        days = max(1, min(10, (to_date.date() - from_date.date()).days + 1))
        bounds = "68,6,98,38" if area == "India" else area
        url = f"{settings.FIRMS_API_URL.rstrip('/')}/{key}/VIIRS_NOAA20_NRT/{bounds}/{days}/{from_date.date().isoformat()}"
        try:
            resp = httpx.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as exc:
            # Do not expose the URL: it contains the FIRMS key.
            raise ProviderUnavailable("FIRMS request failed") from exc
        records, self.validation_report = self.parse_with_report(resp.text)
        return records

    @staticmethod
    def parse_with_report(csv_text: str) -> tuple[list[dict], dict]:
        import pandas as pd
        from app.ml.data.preprocessing import normalize_firms
        try:
            frame = pd.read_csv(io.StringIO(csv_text), dtype=str)
            clean, rejected, report = normalize_firms(frame)
        except (ValueError, pd.errors.ParserError) as exc:
            raise ProviderUnavailable("Invalid FIRMS CSV response") from exc
        if report["missing_columns"]:
            raise ProviderUnavailable("FIRMS response missing required schema")
        records = []
        for row in clean.to_dict("records"):
            # Legacy ORM requires numeric thermal values. Reject explicitly here;
            # the offline event pipeline retains these nullable measurements.
            if pd.isna(row["brightness"]) or pd.isna(row["frp"]):
                report["issues"].append({"source_row": row["source_row"], "reasons": ["legacy_ingest_requires_thermal_values"]})
                report["accepted_rows"] -= 1
                report["rejected_rows"] += 1
                continue
            native = row.get("confidence")
            try:
                confidence = float(native) / 100.0
                confidence = confidence if 0 <= confidence <= 1 else 0.0
            except (ValueError, TypeError):
                confidence = 0.0  # categorical VIIRS confidence has no calibrated numeric equivalent
            records.append({
                "external_id": row["detection_id"], "latitude": row["latitude"],
                "longitude": row["longitude"], "acq_time": row["acquisition_time"].isoformat(),
                "brightness": row["brightness"], "frp": row["frp"],
                "confidence": confidence, "confidence_native": native,
                "satellite": row["satellite"] if pd.notna(row["satellite"]) else "unknown",
                "instrument": row["instrument"],
                "daynight": row["daynight"] if pd.notna(row["daynight"]) else "U", "source": "firms",
            })
        return records, report

    @staticmethod
    def _parse(csv_text: str) -> list[dict]:
        records, report = FirmsProvider.parse_with_report(csv_text)
        if report["rejected_rows"]:
            import logging
            logging.getLogger(__name__).warning("FIRMS validation: %s", report)
        return records


class DemoFireDataProvider(FireDataProvider):
    name = "NASA FIRMS"
    mode = "demo"

    def fetch(self, area: str = "India", from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> list[dict]:
        """Deterministic FIRMS-like detections clustered around industrial zones."""
        rng = random.Random(2024)
        now = datetime.now(timezone.utc)
        records = []
        for zone in INDUSTRIAL_ZONES[:40]:
            code, name, ztype, zlat, zlon, state, district = zone
            n = rng.randint(1, 3)
            for _ in range(n):
                lat = zlat + rng.uniform(-0.05, 0.05)
                lon = zlon + rng.uniform(-0.05, 0.05)
                hours_ago = rng.uniform(1, 48)
                persistent = rng.random() < 0.5
                records.append(
                    {
                        "external_id": f"DEMO_{rng.randint(100000, 999999)}",
                        "latitude": round(lat, 5),
                        "longitude": round(lon, 5),
                        "acq_time": (now - timedelta(hours=hours_ago)).isoformat(),
                        "brightness": round(rng.uniform(320, 400), 1),
                        "frp": round(rng.uniform(15, 120) if persistent else rng.uniform(30, 150), 2),
                        "confidence": round(rng.uniform(0.6, 1.0), 2),
                        "satellite": rng.choice(["VIIRS S-NPP", "VIIRS NOAA-21", "MODIS Aqua"]),
                        "daynight": rng.choice(["D", "D", "N"]),
                        "source": "demo",
                    }
                )
        return records


class UnavailableFireProvider(FireDataProvider):
    name = "NASA FIRMS unavailable"
    mode = "unavailable"

    def fetch(self, *args, **kwargs):
        raise ProviderUnavailable("FIRMS credentials are not configured; demo fallback is disabled")


def get_fire_provider() -> FireDataProvider:
    if settings.firms_api_key:
        return FirmsProvider()
    return DemoFireDataProvider() if settings.DEMO_MODE else UnavailableFireProvider()