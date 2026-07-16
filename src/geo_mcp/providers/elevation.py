"""Open-Elevation provider."""

from __future__ import annotations

from ..http import get_client
from ..validation import validate_coords
from .base import ElevationProvider, _mock, get_quota_tracker, is_dry_run


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
            if len(c) < 2:
                raise ValueError(f"Each coordinate must be [lon, lat], got {c}")
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
