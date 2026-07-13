"""Provider plugin system for geocoding, routing, and elevation.

Each provider implements a simple ABC.  The active provider is selected via
environment variables (GEO_MCP_GEOCODING_PROVIDER, GEO_MCP_ROUTING_PROVIDER,
GEO_MCP_ELEVATION_PROVIDER).  Defaults are Nominatim, OSRM, and
Open-Elevation respectively — all free, no API key required.

To add a new provider (e.g. Mapbox, Google), subclass the relevant ABC and
register it in the PROVIDER_REGISTRY below.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .config import settings
from .http import get_client, nominatim_limiter
from .validation import validate_coords


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


class NominatimProvider(GeocodingProvider):
    """Default geocoding provider using OpenStreetMap Nominatim."""

    async def geocode(self, query: str, *, limit: int, countrycodes: str | None) -> list[dict]:
        if is_dry_run():
            return _mock.geocode_result[:limit]
        get_quota_tracker("nominatim").record()
        params: dict = {
            "q": query,
            "format": "jsonv2",
            "limit": min(limit, settings.geocode_result_limit),
            "addressdetails": 1,
        }
        if countrycodes:
            params["countrycodes"] = countrycodes
        limiter = nominatim_limiter()
        async with get_client() as client:
            await limiter.acquire()
            resp = await client.get(f"{settings.nominatim_url}/search", params=params)
            resp.raise_for_status()
            results = resp.json()
        return [
            {
                "name": r.get("display_name", ""),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "bbox": [
                    float(r["boundingbox"][2]),
                    float(r["boundingbox"][0]),
                    float(r["boundingbox"][3]),
                    float(r["boundingbox"][1]),
                ],
                "osm_type": r.get("osm_type"),
                "osm_id": r.get("osm_id"),
                "importance": float(r.get("importance", 0)),
            }
            for r in results
        ]

    async def reverse_geocode(self, lat: float, lon: float, *, zoom: int) -> dict:
        if is_dry_run():
            return _mock.reverse_geocode_result
        validate_coords(lon, lat)
        get_quota_tracker("nominatim").record()
        params: dict[str, str | int | float] = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "zoom": zoom,
            "addressdetails": 1,
        }
        limiter = nominatim_limiter()
        async with get_client() as client:
            await limiter.acquire()
            resp = await client.get(f"{settings.nominatim_url}/reverse", params=params)
            resp.raise_for_status()
            data = resp.json()
        return {
            "display_name": data.get("display_name", ""),
            "address": data.get("address", {}),
            "lat": float(data.get("lat", lat)),
            "lon": float(data.get("lon", lon)),
            "osm_type": data.get("osm_type"),
            "osm_id": data.get("osm_id"),
        }


class OSRMProvider(RoutingProvider):
    """Default routing provider using OSRM."""

    async def route(self, coordinates: list[list[float]], *, profile: str) -> dict:
        if is_dry_run():
            return _mock.route_result
        get_quota_tracker("osrm").record()
        coords_str = ";".join(f"{lon},{lat}" for lon, lat in coordinates)
        url = f"{settings.osrm_url}/route/v1/{profile}/{coords_str}"
        params = {"overview": "full", "geometries": "geojson", "steps": "false"}
        async with get_client() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if data["code"] != "Ok":
            return {"error": f"OSRM returned: {data.get('code')}", "message": data.get("message", "")}
        route_data = data["routes"][0]
        return {
            "distance_m": route_data["distance"],
            "duration_s": route_data["duration"],
            "geometry": route_data["geometry"],
        }

    async def route_matrix(
        self, sources: list[list[float]], destinations: list[list[float]], *, profile: str
    ) -> dict:
        if is_dry_run():
            return {"durations": [[0, 900], [900, 0]], "distances": [[0, 12500], [12500, 0]]}
        get_quota_tracker("osrm").record()
        sources_str = ";".join(f"{lon},{lat}" for lon, lat in sources)
        dests_str = ";".join(f"{lon},{lat}" for lon, lat in destinations)
        url = f"{settings.osrm_url}/table/v1/{profile}/{sources_str};{dests_str}"
        num_src = len(sources)
        num_dest = len(destinations)
        params = {
            "sources": ";".join(str(i) for i in range(num_src)),
            "destinations": ";".join(str(i) for i in range(num_src, num_src + num_dest)),
            "annotations": "duration,distance",
        }
        async with get_client() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if data["code"] != "Ok":
            return {"error": f"OSRM returned: {data.get('code')}", "message": data.get("message", "")}
        return {
            "durations": data.get("durations", []),
            "distances": data.get("distances", []),
        }

    async def nearest_road(self, lat: float, lon: float, *, profile: str) -> dict:
        if is_dry_run():
            return {"lat": lat, "lon": lon, "name": "Mock Road", "distance_m": 5.0}
        validate_coords(lon, lat)
        get_quota_tracker("osrm").record()
        url = f"{settings.osrm_url}/nearest/v1/{profile}/{lon},{lat}"
        async with get_client() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        if data["code"] != "Ok":
            return {"error": f"OSRM returned: {data.get('code')}", "message": data.get("message", "")}
        wp = data["waypoints"][0]
        return {
            "lat": wp["location"][1],
            "lon": wp["location"][0],
            "name": wp.get("name", ""),
            "distance_m": wp.get("distance", 0),
        }


class OpenElevationProvider(ElevationProvider):
    """Default elevation provider using Open-Elevation API."""

    async def elevation(self, lat: float, lon: float) -> dict:
        if is_dry_run():
            return _mock.elevation_result
        validate_coords(lon, lat)
        get_quota_tracker("open_elevation").record()
        async with get_client() as client:
            resp = await client.get(
                "https://api.open-elevation.com/api/v1/lookup",
                params={"latitude": lat, "longitude": lon},
            )
            resp.raise_for_status()
            data = resp.json()
        results = data.get("results") or [data]
        if not results:
            raise ValueError("Elevation provider returned no results")
        result = results[0]
        return {
            "lat": result.get("latitude", lat),
            "lon": result.get("longitude", lon),
            "elevation_m": result.get("elevation"),
        }

    async def elevation_profile(self, coordinates: list[list[float]]) -> list[dict]:
        if is_dry_run():
            return [
                {"lat": c[1], "lon": c[0], "elevation_m": 45.0 + i * 2}
                for i, c in enumerate(coordinates)
            ]
        get_quota_tracker("open_elevation").record()
        for c in coordinates:
            validate_coords(c[0], c[1])
        points = [{"latitude": c[1], "longitude": c[0]} for c in coordinates]
        async with get_client() as client:
            resp = await client.post(
                "https://api.open-elevation.com/api/v1/lookup",
                json={"locations": points},
            )
            resp.raise_for_status()
            data = resp.json()
        return [
            {
                "lat": r.get("latitude"),
                "lon": r.get("longitude"),
                "elevation_m": r.get("elevation"),
            }
            for r in data.get("results", [])
        ]


PROVIDER_REGISTRY: dict[str, dict[str, type]] = {
    "geocoding": {
        "nominatim": NominatimProvider,
    },
    "routing": {
        "osrm": OSRMProvider,
    },
    "elevation": {
        "open_elevation": OpenElevationProvider,
    },
}


def get_geocoding_provider() -> GeocodingProvider:
    name = getattr(settings, "geocoding_provider", "nominatim")
    cls = PROVIDER_REGISTRY["geocoding"].get(name)
    if cls is None:
        raise ValueError(
            f"Unknown geocoding provider '{name}'. "
            f"Available: {sorted(PROVIDER_REGISTRY['geocoding'])}"
        )
    return cls()  # type: ignore[no-any-return]


def get_routing_provider() -> RoutingProvider:
    name = getattr(settings, "routing_provider", "osrm")
    cls = PROVIDER_REGISTRY["routing"].get(name)
    if cls is None:
        raise ValueError(
            f"Unknown routing provider '{name}'. "
            f"Available: {sorted(PROVIDER_REGISTRY['routing'])}"
        )
    return cls()  # type: ignore[no-any-return]


def get_elevation_provider() -> ElevationProvider:
    name = getattr(settings, "elevation_provider", "open_elevation")
    cls = PROVIDER_REGISTRY["elevation"].get(name)
    if cls is None:
        raise ValueError(
            f"Unknown elevation provider '{name}'. "
            f"Available: {sorted(PROVIDER_REGISTRY['elevation'])}"
        )
    return cls()  # type: ignore[no-any-return]


def list_providers() -> dict:
    """Return all registered providers grouped by service type."""
    return {
        service: {
            name: {"class": cls.__name__, "module": cls.__module__}
            for name, cls in providers.items()
        }
        for service, providers in PROVIDER_REGISTRY.items()
    }
