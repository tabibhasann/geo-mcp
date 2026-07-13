"""Nominatim geocoding provider using OpenStreetMap."""

from __future__ import annotations

from ..config import settings
from ..http import get_client, nominatim_limiter
from ..validation import validate_coords
from .base import GeocodingProvider, _mock, get_quota_tracker, is_dry_run


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
