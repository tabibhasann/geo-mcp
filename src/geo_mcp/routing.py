"""Routing tools using OSRM (Open Source Routing Machine)."""

import json

from .config import settings
from .errors import async_safe_tool
from .http import get_client
from .validation import validate_coords


def _parse_coordinates(coords: str | list) -> list[list[float]]:
    """Parse and validate a list of [lon, lat] coordinates."""
    parsed = json.loads(coords) if isinstance(coords, str) else coords
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("Coordinates must be a non-empty array of [lon, lat] pairs")

    coordinates = []
    for coord in parsed:
        if not isinstance(coord, list | tuple) or len(coord) != 2:
            raise ValueError("Each coordinate must be [lon, lat]")
        lon = float(coord[0])
        lat = float(coord[1])
        validate_coords(lon, lat)
        coordinates.append([lon, lat])
    return coordinates


def _to_lonlat_string(coords: list[list[float]]) -> str:
    """Convert [lon, lat] pairs to an OSRM coordinate string."""
    return ";".join(f"{lon},{lat}" for lon, lat in coords)


@async_safe_tool
async def route(
    coordinates: str | list,
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

    parsed_coordinates = _parse_coordinates(coordinates)
    if len(parsed_coordinates) < 2:
        raise ValueError("Route requires at least two coordinates")

    coords_str = _to_lonlat_string(parsed_coordinates)
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
    sources: str | list,
    destinations: str | list,
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

    src_list = _parse_coordinates(sources)
    dest_list = _parse_coordinates(destinations)
    sources_str = _to_lonlat_string(src_list)
    dests_str = _to_lonlat_string(dest_list)
    url = f"{settings.osrm_url}/table/v1/{profile}/{sources_str};{dests_str}"
    num_src = len(src_list)
    num_dest = len(dest_list)
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
    validate_coords(lon, lat)
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
