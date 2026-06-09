"""Elevation lookup tools using Open-Elevation API."""

import json

from .errors import async_safe_tool
from .http import get_client
from .validation import validate_coords


@async_safe_tool
async def elevation(
    lat: float,
    lon: float,
) -> dict:
    """Get elevation (metres above sea level) for a coordinate.

    Uses the Open-Elevation public API (free, no key required).

    Returns {lat, lon, elevation_m}.
    """
    validate_coords(lon, lat)

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


@async_safe_tool
async def elevation_profile(
    coordinates: str,
) -> list[dict]:
    """Get elevation at multiple points along a path.

    coordinates: JSON array of [lon, lat] pairs.

    Returns a list of {lat, lon, elevation_m} for each point.
    """
    coords = json.loads(coordinates) if isinstance(coordinates, str) else coordinates
    if len(coords) < 2:
        raise ValueError("Need at least 2 coordinate pairs for a profile")

    for c in coords:
        validate_coords(c[0], c[1])

    points = [{"latitude": c[1], "longitude": c[0]} for c in coords]

    async with get_client() as client:
        resp = await client.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json={"locations": points},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for r in data.get("results", []):
        results.append(
            {
                "lat": r.get("latitude"),
                "lon": r.get("longitude"),
                "elevation_m": r.get("elevation"),
            }
        )
    return results
