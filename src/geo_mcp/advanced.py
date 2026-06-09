"""Advanced spatial tools for larger geospatial workflows."""

import json
from collections import OrderedDict
from copy import deepcopy
from numbers import Integral
from typing import Any

from shapely.strtree import STRtree
from shapely.validation import explain_validity

from .errors import async_safe_tool, safe_tool
from .geocoding import geocode
from .geometry import parse, serialize

_PREDICATES = {
    "intersects": lambda geom, query: geom.intersects(query),
    "within": lambda geom, query: geom.within(query),
    "contains": lambda geom, query: geom.contains(query),
    "touches": lambda geom, query: geom.touches(query),
    "overlaps": lambda geom, query: geom.overlaps(query),
    "crosses": lambda geom, query: geom.crosses(query),
}


def _feature_collection(geojson_collection: str) -> dict[str, Any]:
    data = json.loads(geojson_collection)
    if data.get("type") != "FeatureCollection":
        raise ValueError("Input must be a GeoJSON FeatureCollection")
    return data


def _feature_geometries(features: list[dict[str, Any]]) -> list[Any]:
    geometries = []
    for feature in features:
        geometry = feature.get("geometry")
        if geometry is not None:
            geometries.append(parse(json.dumps(geometry)))
    return geometries


def _json_feature_collection(features: list[dict[str, Any]]) -> str:
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)


@safe_tool
def build_spatial_index(geojson_collection: str) -> dict:
    """Build a Shapely STRtree spatial index for a GeoJSON FeatureCollection."""
    data = _feature_collection(geojson_collection)
    features = data.get("features", [])
    geometries = _feature_geometries(features)

    bounds = None
    node_capacity = None
    if geometries:
        tree = STRtree(geometries)
        minx = min(geom.bounds[0] for geom in geometries)
        miny = min(geom.bounds[1] for geom in geometries)
        maxx = max(geom.bounds[2] for geom in geometries)
        maxy = max(geom.bounds[3] for geom in geometries)
        bounds = [minx, miny, maxx, maxy]
        node_capacity = getattr(tree, "node_capacity", None)

    return {
        "feature_count": len(features),
        "indexed_geometry_count": len(geometries),
        "index_type": "STRtree",
        "bounds": bounds,
        "node_capacity": node_capacity,
    }


@safe_tool
def spatial_query(geojson_collection: str, query_geojson: str, predicate: str = "intersects") -> str:
    """Query a GeoJSON FeatureCollection using spatial predicates."""
    if predicate not in _PREDICATES:
        raise ValueError(f"Unknown predicate: {predicate}. Supported: {sorted(_PREDICATES)}")

    data = _feature_collection(geojson_collection)
    features = data.get("features", [])
    geometries = []
    feature_by_geom_id = {}
    for feature in features:
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        geom = parse(json.dumps(geometry))
        geometries.append(geom)
        feature_by_geom_id[id(geom)] = feature

    if not geometries:
        return _json_feature_collection([])

    query_geom = parse(query_geojson)
    tree = STRtree(geometries)
    candidates = tree.query(query_geom)

    results: list[dict[str, Any]] = []
    for candidate in candidates:
        geom = geometries[int(candidate)] if isinstance(candidate, Integral) else candidate
        feature = feature_by_geom_id[id(geom)]
        if _PREDICATES[predicate](geom, query_geom):
            results.append(feature)

    return _json_feature_collection(results)


@safe_tool
def spatial_join(points_geojson: str, polygons_geojson: str) -> str:
    """Join point features to the first polygon that contains each point."""
    points_data = _feature_collection(points_geojson)
    polygons_data = _feature_collection(polygons_geojson)

    polygon_features = polygons_data.get("features", [])
    polygon_geoms = []
    feature_by_geom_id = {}
    for feature in polygon_features:
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        geom = parse(json.dumps(geometry))
        polygon_geoms.append(geom)
        feature_by_geom_id[id(geom)] = feature

    tree = STRtree(polygon_geoms) if polygon_geoms else None
    result_features = []

    for point_feature in points_data.get("features", []):
        point_geom = parse(json.dumps(point_feature["geometry"]))
        polygon_id = None

        if tree is not None:
            candidates = tree.query(point_geom)
            for candidate in candidates:
                geom = polygon_geoms[int(candidate)] if isinstance(candidate, Integral) else candidate
                if geom.contains(point_geom):
                    polygon_feature = feature_by_geom_id[id(geom)]
                    polygon_id = (
                        polygon_feature.get("id")
                        or polygon_feature.get("properties", {}).get("polygon_id")
                        or polygon_feature.get("properties", {}).get("id")
                    )
                    break

        new_feature = deepcopy(point_feature)
        new_feature["properties"] = dict(point_feature.get("properties", {}))
        new_feature["properties"]["polygon_id"] = polygon_id
        result_features.append(new_feature)

    return _json_feature_collection(result_features)


_geocode_cache: OrderedDict[str, Any] = OrderedDict()


@async_safe_tool
async def cached_geocode(address: str, limit: int = 1) -> dict:
    """Geocode an address and cache the result in memory for this server process."""
    cache_key = f"{address}|{limit}"

    if cache_key in _geocode_cache:
        payload = deepcopy(_geocode_cache[cache_key])
        _geocode_cache.move_to_end(cache_key)
        return {"address": address, "cached": True, "matches": payload}

    matches = await geocode(address, limit=limit)
    if len(_geocode_cache) >= 1000:
        _geocode_cache.popitem(last=False)

    _geocode_cache[cache_key] = deepcopy(matches)
    return {"address": address, "cached": False, "matches": matches}


@async_safe_tool
async def batch_geocode(addresses: list[str], limit: int = 1) -> dict:
    """Geocode multiple addresses with cache metadata for each item."""
    results = []
    cache_hits = 0

    for index, address in enumerate(addresses):
        result = await cached_geocode(address, limit=limit)
        if result.get("cached"):
            cache_hits += 1
        results.append({"address": address, "index": index, "result": result})

    return {
        "total": len(addresses),
        "cache_hits": cache_hits,
        "cache_misses": len(addresses) - cache_hits,
        "results": results,
    }


@safe_tool
def nearest_neighbor(query_geojson: str, candidates_geojson: str, k: int = 1) -> str:
    """Find the nearest features to a query geometry."""
    if k <= 0:
        raise ValueError("k must be positive")

    query_geom = parse(query_geojson)
    candidates_data = _feature_collection(candidates_geojson)
    features = candidates_data.get("features", [])

    distances = []
    for feature in features:
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        geom = parse(json.dumps(geometry))
        distances.append((query_geom.distance(geom), feature))

    result_features = []
    for distance, feature in sorted(distances, key=lambda item: item[0])[:k]:
        new_feature = deepcopy(feature)
        new_feature["properties"] = dict(feature.get("properties", {}))
        new_feature["properties"]["distance_to_query"] = distance
        result_features.append(new_feature)

    return _json_feature_collection(result_features)


@safe_tool
def repair_geometry(geojson: str) -> str:
    """Repair an invalid geometry using Shapely's zero-width buffer fallback."""
    geom = parse(geojson)
    if geom.is_valid:
        return serialize(geom, indent=2)

    repaired = geom.buffer(0)
    return serialize(repaired, indent=2)


@safe_tool
def validate_geometry(geojson: str) -> dict:
    """Validate a geometry and report issues that a caller can act on."""
    try:
        geom = parse(geojson)
    except Exception as e:
        return {
            "is_valid": False,
            "parseable": False,
            "error": str(e),
            "can_repair": False,
        }

    issues = []
    if not geom.is_valid:
        issues.append(explain_validity(geom))
    if geom.is_empty:
        issues.append("Geometry is empty")
    if hasattr(geom, "is_simple") and not geom.is_simple:
        issues.append("Geometry is not simple")

    return {
        "is_valid": bool(geom.is_valid),
        "parseable": True,
        "geometry_type": geom.geom_type,
        "issues": issues,
        "can_repair": (not geom.is_valid) and geom.geom_type in {"Polygon", "MultiPolygon"},
    }
