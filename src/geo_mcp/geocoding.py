"""Geocoding tools using Nominatim (OpenStreetMap)."""

from .config import settings
from .errors import async_safe_tool
from .http import get_client, nominatim_limiter
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
