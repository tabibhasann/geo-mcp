"""Elevation tools — delegate to the configured provider."""

import json

from .errors import async_safe_tool
from .providers import get_elevation_provider
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
    provider = get_elevation_provider()
    return await provider.elevation(lat, lon)


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

    provider = get_elevation_provider()
    return await provider.elevation_profile(coords)
