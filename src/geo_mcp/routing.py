"""Routing tools — delegate to the configured provider."""

import json

from .errors import async_safe_tool
from .providers import get_routing_provider
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

    provider = get_routing_provider()
    return await provider.route(parsed_coordinates, profile=profile)


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

    provider = get_routing_provider()
    return await provider.route_matrix(src_list, dest_list, profile=profile)


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

    provider = get_routing_provider()
    return await provider.nearest_road(lat, lon, profile=profile)
