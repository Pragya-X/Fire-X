"""Small shared utilities."""
from __future__ import annotations

import time

CLASSIFICATIONS = [
    "Industrial Fire",
    "Persistent Industrial Heat Source",
    "Gas Flare",
    "Wildfire",
    "Agricultural Burning",
    "Other Thermal Anomaly",
]

RISK_LEVELS = [
    ("LOW", 0, 20),
    ("MODERATE", 21, 40),
    ("ELEVATED", 41, 60),
    ("HIGH", 61, 80),
    ("CRITICAL", 81, 100),
]


def risk_level_for(score: float) -> str:
    for name, lo, hi in RISK_LEVELS:
        if lo <= score <= hi:
            return name
    return "LOW"


def clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


class Timer:
    def __init__(self) -> None:
        self.start = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.start) * 1000)
