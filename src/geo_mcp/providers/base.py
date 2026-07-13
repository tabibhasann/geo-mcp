"""Base classes and shared utilities for provider plugins."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..config import settings


@dataclass
class QuotaTracker:
    """Track API calls per provider and warn when approaching limits."""

    provider_name: str
    daily_limit: int = 0  # 0 = unlimited
    _call_count: int = 0
    _warned_80: bool = False
    _warned_100: bool = False

    def record(self) -> None:
        self._call_count += 1
        if self.daily_limit <= 0:
            return
        pct = (self._call_count / self.daily_limit) * 100
        if pct >= 100 and not self._warned_100:
            self._warned_100 = True
            raise RuntimeError(
                f"{self.provider_name}: daily limit reached ({self.daily_limit} calls). "
                f"Set GEO_MCP_{self.provider_name.upper()}_DAILY_LIMIT to increase."
            )
        if pct >= 80 and not self._warned_80:
            self._warned_80 = True
            print(
                f"Warning: {self.provider_name} quota at {pct:.0f}% "
                f"({self._call_count}/{self.daily_limit})",
                file=sys.stderr,
            )

    @property
    def call_count(self) -> int:
        return self._call_count


@dataclass
class MockData:
    """Deterministic mock responses for --dry-run mode."""

    geocode_result: list[dict] = field(default_factory=lambda: [
        {
            "name": "Mock City, Mock Country",
            "lat": 23.8103,
            "lon": 90.4125,
            "bbox": [90.3, 23.7, 90.5, 23.9],
            "osm_type": "node",
            "osm_id": 123456,
            "importance": 0.8,
        }
    ])
    reverse_geocode_result: dict = field(default_factory=lambda: {
        "display_name": "Mock Address 123",
        "address": {"city": "Mock City", "country": "Mock Country"},
        "lat": 23.8103,
        "lon": 90.4125,
        "osm_type": "node",
        "osm_id": 123456,
    })
    route_result: dict = field(default_factory=lambda: {
        "distance_m": 12500.0,
        "duration_s": 900.0,
        "geometry": {"type": "LineString", "coordinates": [[90.41, 23.81], [90.42, 23.82]]},
    })
    elevation_result: dict = field(default_factory=lambda: {
        "lat": 23.8103,
        "lon": 90.4125,
        "elevation_m": 45.0,
    })


_mock = MockData()
_quota_trackers: dict[str, QuotaTracker] = {}


def get_quota_tracker(provider_name: str) -> QuotaTracker:
    if provider_name not in _quota_trackers:
        limit = getattr(settings, f"{provider_name.lower()}_daily_limit", 0)
        _quota_trackers[provider_name] = QuotaTracker(provider_name, daily_limit=limit)
    return _quota_trackers[provider_name]


def is_dry_run() -> bool:
    return getattr(settings, "dry_run", False)


class GeocodingProvider(ABC):
    @abstractmethod
    async def geocode(self, query: str, *, limit: int, countrycodes: str | None) -> list[dict]:
        ...

    @abstractmethod
    async def reverse_geocode(self, lat: float, lon: float, *, zoom: int) -> dict:
        ...


class RoutingProvider(ABC):
    @abstractmethod
    async def route(self, coordinates: list[list[float]], *, profile: str) -> dict:
        ...

    @abstractmethod
    async def route_matrix(
        self, sources: list[list[float]], destinations: list[list[float]], *, profile: str
    ) -> dict:
        ...

    @abstractmethod
    async def nearest_road(self, lat: float, lon: float, *, profile: str) -> dict:
        ...


class ElevationProvider(ABC):
    @abstractmethod
    async def elevation(self, lat: float, lon: float) -> dict:
        ...

    @abstractmethod
    async def elevation_profile(self, coordinates: list[list[float]]) -> list[dict]:
        ...
