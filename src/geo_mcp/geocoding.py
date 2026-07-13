"""Geocoding tools — delegate to the configured provider."""

from .errors import async_safe_tool
from .providers import get_geocoding_provider
from .validation import validate_coords


@async_safe_tool
async def geocode(
    query: str,
    *,
    limit: int = 5,
    countrycodes: str | None = None,
) -> list[dict]:
    """Forward geocode an address or place name to coordinates.

    Returns a list of matches with name, lat, lon, bounding box, OSM type,
    and importance score, sorted most relevant first.
    """
    provider = get_geocoding_provider()
    return await provider.geocode(query, limit=limit, countrycodes=countrycodes)


@async_safe_tool
async def reverse_geocode(
    lat: float,
    lon: float,
    *,
    zoom: int = 18,
) -> dict:
    """Reverse geocode coordinates to the nearest address or place.

    Returns a structured address and display name.
    """
    validate_coords(lon, lat)
    provider = get_geocoding_provider()
    return await provider.reverse_geocode(lat, lon, zoom=zoom)
