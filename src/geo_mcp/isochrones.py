"""Isochrone tools — compute reachable areas within time/distance limits."""

from .config import settings
from .errors import async_safe_tool
from .http import get_client
from .validation import validate_coords, validate_positive

_VALID_PROFILES = {
    "driving-car",
    "driving-hgv",
    "foot-walking",
    "foot-hiking",
    "cycling-regular",
    "cycling-road",
    "cycling-mountain",
    "cycling-electric",
    "wheelchair",
}


@async_safe_tool
async def isochrone(
    lat: float,
    lon: float,
    *,
    range_value: float = 300,
    range_type: str = "time",
    profile: str = "driving-car",
) -> dict:
    """Compute an isochrone (reachable area) from a point.

    Args:
        lat: Latitude of the starting point.
        lon: Longitude of the starting point.
        range_value: Range limit. For time: seconds (default 300 = 5 min).
            For distance: metres (default 300 m).
        range_type: "time" (seconds) or "distance" (metres).
        profile: Routing profile. Options: "driving-car", "driving-hgv",
                "foot-walking", "foot-hiking", "cycling-regular",
                "cycling-road", "cycling-mountain", "cycling-electric",
                "wheelchair".

    Returns:
        GeoJSON FeatureCollection with isochrone polygons.

    Note:
        Requires GEO_MCP_ORS_API_KEY environment variable.
        Get a free key at https://openrouteservice.org/dev/#/signup
    """
    validate_coords(lon, lat)
    validate_positive(range_value, "range_value")

    valid_range_types = {"time", "distance"}
    if range_type not in valid_range_types:
        raise ValueError(f"range_type must be one of {valid_range_types}")
    if profile not in _VALID_PROFILES:
        raise ValueError(f"profile must be one of {sorted(_VALID_PROFILES)}")

    if not settings.ors_api_key:
        raise ValueError(
            "Isochrones require an OpenRouteService API key. "
            "Set GEO_MCP_ORS_API_KEY environment variable. "
            "Get a free key at https://openrouteservice.org/dev/#/signup"
        )

    url = f"{settings.ors_url}/v2/isochrones/{profile}"
    payload = {
        "locations": [[lon, lat]],
        "range": [range_value],
        "range_type": range_type,
    }

    async with get_client() as client:
        resp = await client.post(
            url,
            json=payload,
            headers={
                "Authorization": settings.ors_api_key,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # ORS returns GeoJSON FeatureCollection
    features = data.get("features", [])
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "center": [lon, lat],
            "range_value": range_value,
            "range_type": range_type,
            "profile": profile,
            "unit": "seconds" if range_type == "time" else "metres",
        },
    }
