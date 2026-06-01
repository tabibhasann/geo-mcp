"""OpenStreetMap / Overpass query tools.

This is the flagship feature: build safe Overpass QL queries and execute them
to retrieve OSM features as GeoJSON.
"""

import contextlib
import json

import httpx

from .config import settings
from .errors import async_safe_tool, safe_tool


@safe_tool
def build_overpass_query(
    area: str | list[float],
    tags: dict[str, str],
    *,
    element_types: list[str] | None = None,
) -> str:
    """Build a safe Overpass QL query string (no network call).

    area can be:
      - A bbox: [south, west, north, east]
      - A place name like "Dhaka, Bangladesh" (resolved via geocoding first)
      - A GeoJSON polygon string (will be serialized as poly)

    tags are OSM tag key-value pairs, e.g., {"amenity": "hospital"}.
    element_types: ["node", "way", "relation"] (default: all three).
    """
    if element_types is None:
        element_types = ["node", "way", "relation"]

    # Build tag filter
    tag_filters = []
    if isinstance(tags, dict):
        for k, v in tags.items():
            if v:
                tag_filters.append(f'["{k}"="{v}"]')
            else:
                tag_filters.append(f'["{k}"]')
    else:
        raise ValueError("tags must be a dict of OSM key-value pairs")

    tag_str = "".join(tag_filters)

    # Build area clause
    if isinstance(area, list):
        if len(area) != 4:
            raise ValueError("area bbox must be [south, west, north, east]")
        s, w, n, e = area
        area_clause = f"({s},{w},{n},{e})"
    elif isinstance(area, str):
        try:
            data = json.loads(area) if area.strip().startswith("{") else None
        except (json.JSONDecodeError, TypeError):
            data = None

        if data is not None and data.get("coordinates"):
            # It's a GeoJSON geometry — use poly: filter
            return _build_poly_query(data, tag_str, element_types)

        # Treat as a place name — use nominatim area lookup
        return _build_area_query(area, tag_str, element_types)
    else:
        raise ValueError("area must be a bbox [s,w,n,e], a place name string, or GeoJSON polygon")

    types_str = " ".join(element_types)
    return f"""
[out:json][timeout:{int(settings.overpass_timeout)}];
{types_str}{tag_str}{area_clause};
out body {settings.osm_result_limit};
out skel qt;
"""


def _build_area_query(place_name: str, tag_str: str, element_types: list[str]) -> str:
    """Build a query using an area by name (assumes nominatim resolves first)."""
    types_str = " ".join(element_types)
    escaped = place_name.replace('"', '\\"')
    return f"""
[out:json][timeout:{int(settings.overpass_timeout)}];
area["name"="{escaped}"]->.searchArea;
{types_str}{tag_str}(area.searchArea);
out body {settings.osm_result_limit};
out skel qt;
"""


def _build_poly_query(geojson: dict, tag_str: str, element_types: list[str]) -> str:
    """Build an Overpass QL query using a polygon filter from GeoJSON."""
    coords = _extract_coords(geojson)
    if not coords:
        raise ValueError("Could not extract coordinates from GeoJSON")

    poly = " ".join(f"{lat} {lon}" for lon, lat in coords)
    types_str = " ".join(element_types)
    return f"""
[out:json][timeout:{int(settings.overpass_timeout)}];
{types_str}{tag_str}(poly:"{poly}");
out body {settings.osm_result_limit};
out skel qt;
"""


def _extract_coords(geojson: dict) -> list[tuple[float, float]]:
    """Extract polygon exterior ring coordinates from GeoJSON."""
    geom_type = geojson.get("type", "")
    coords = geojson.get("coordinates", [])

    if geom_type == "Polygon":
        return [(c[0], c[1]) for c in coords[0]]
    elif geom_type == "MultiPolygon":
        # Use the largest polygon
        largest = max(coords, key=lambda ring: len(ring[0]))
        return [(c[0], c[1]) for c in largest[0]]
    elif geom_type in ("GeometryCollection",):
        for geom in geojson.get("geometries", []):
            if geom.get("type") in ("Polygon", "MultiPolygon"):
                return _extract_coords(geom)
    return []


def _osm_element_to_feature(element: dict) -> dict:
    """Convert an Overpass API element to a GeoJSON Feature."""
    etype = element.get("type", "")
    eid = element.get("id")
    tags = element.get("tags", {})
    name = tags.get("name", tags.get("ref", f"{etype}/{eid}"))

    if "lat" in element and "lon" in element:
        geometry = {"type": "Point", "coordinates": [element["lon"], element["lat"]]}
    elif "center" in element:
        c = element["center"]
        geometry = {"type": "Point", "coordinates": [c["lon"], c["lat"]]}
    elif "geometry" in element:
        geometry = element["geometry"]
    else:
        geometry = None

    return {
        "type": "Feature",
        "id": f"{etype}/{eid}",
        "geometry": geometry,
        "properties": {
            "osm_type": etype,
            "osm_id": eid,
            "name": name,
            "tags": tags,
        },
    }


@async_safe_tool
async def osm_features(
    area: str,
    tags: str,
    *,
    limit: int = 200,
) -> dict:
    """Find OSM features matching tags within an area.

    area: bbox [s,w,n,e] as JSON string, place name string, or GeoJSON polygon.
    tags: JSON object of OSM tag key-value pairs, e.g., '{"amenity":"hospital"}'.

    Returns a GeoJSON FeatureCollection.
    """
    import json as _json

    tags_dict = tags if isinstance(tags, dict) else _json.loads(tags)
    area_val = area
    with contextlib.suppress(_json.JSONDecodeError, TypeError):
        area_val = _json.loads(area)

    ql = build_overpass_query(area_val, tags_dict)
    if isinstance(ql, dict) and "error" in ql:
        return ql

    return await overpass_query(ql, limit=limit)


@async_safe_tool
async def overpass_query(ql_string: str, *, limit: int = 200) -> dict:
    """Execute a raw Overpass QL query and return results as a GeoJSON FeatureCollection.

    Power-user escape hatch — use build_overpass_query for safe query construction.
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": settings.user_agent},
        timeout=httpx.Timeout(settings.overpass_timeout),
    ) as client:
        resp = await client.post(
            settings.overpass_url,
            data={"data": ql_string},
        )
        resp.raise_for_status()
        data = resp.json()

    elements = data.get("elements", [])
    result_limit = min(limit, settings.osm_result_limit)

    features = []
    for el in elements[:result_limit]:
        f = _osm_element_to_feature(el)
        if f["geometry"] is not None:
            features.append(f)

    truncated = len(elements) > result_limit
    result: dict = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_elements": len(elements),
            "returned": len(features),
        },
    }
    if truncated:
        result["metadata"]["truncated"] = True
        result["metadata"]["note"] = (
            f"Results truncated to {result_limit}. Narrow your query to get more."
        )

    return result
