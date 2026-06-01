"""Routing tools using OSRM (Open Source Routing Machine)."""

import json

from .config import settings
from .errors import async_safe_tool
from .http import get_client


def _to_lonlat_string(coords: str | list) -> str:
    """Convert a list of [lon, lat] pairs or JSON string to an OSRM coordinate string."""
    parsed: list = json.loads(coords) if isinstance(coords, str) else coords
    return ";".join(f"{c[0]},{c[1]}" for c in parsed)


@async_safe_tool
async def route(
    coordinates: str,
    *,
    profile: str = "driving",
) -> dict:
    """Compute a route between waypoints.

    coordinates: JSON array of [lon, lat] pairs (at least 2).
    profile: "driving", "walking", or "cycling".

    Returns distance (metres), duration (seconds), and the route geometry as GeoJSON.
    """
    valid_profiles = {"driving", "walking", "cycling"}
    if profile not in valid_profiles:
        raise ValueError(f"Invalid profile: {profile}. Supported: {sorted(valid_profiles)}")

    coords_str = _to_lonlat_string(coordinates)
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


@async_safe_tool
async def route_matrix(
    sources: str,
    destinations: str,
    *,
    profile: str = "driving",
) -> dict:
    """Compute a duration/distance matrix between source and destination points.

    sources: JSON array of [lon, lat] source locations.
    destinations: JSON array of [lon, lat] destination locations.
    profile: "driving", "walking", or "cycling".

    Returns {durations: [[s]], distances: [[m]]}.
    """
    valid_profiles = {"driving", "walking", "cycling"}
    if profile not in valid_profiles:
        raise ValueError(f"Invalid profile: {profile}. Supported: {sorted(valid_profiles)}")

    sources_str = _to_lonlat_string(sources)
    dests_str = _to_lonlat_string(destinations)
    url = f"{settings.osrm_url}/table/v1/{profile}/{sources_str};{dests_str}"
    params = {"sources": "all", "annotations": "duration,distance"}

    # Calculate source indices
    src_list = json.loads(sources) if isinstance(sources, str) else sources
    num_src = len(src_list)
    params["sources"] = ";".join(str(i) for i in range(num_src))

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


@async_safe_tool
async def nearest_road(
    lat: float,
    lon: float,
    *,
    profile: str = "driving",
) -> dict:
    """Snap a coordinate to the nearest road.

    Returns {lat, lon, name} of the nearest road.
    """
    valid_profiles = {"driving", "walking", "cycling"}
    if profile not in valid_profiles:
        raise ValueError(f"Invalid profile: {profile}. Supported: {sorted(valid_profiles)}")

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
