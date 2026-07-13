"""OSRM routing provider."""

from __future__ import annotations

from ..config import settings
from ..http import get_client
from ..validation import validate_coords
from .base import RoutingProvider, _mock, get_quota_tracker, is_dry_run


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
