"""Geometry tools — local, no network operations on GeoJSON."""

import json

from shapely import make_valid
from shapely.validation import explain_validity

from . import units
from .errors import safe_tool


def parse(geojson_str: str):
    """Parse GeoJSON string and return a shapely geometry."""
    return units.geojson_to_shapely(geojson_str)


def serialize(geom, indent: int | None = None) -> str:
    """Serialize a shapely geometry to GeoJSON string."""
    return units.shapely_to_geojson(geom, indent)


@safe_tool
def buffer(geojson: str, distance_m: float, *, quad_segs: int = 8) -> str:
    """Buffer a Geometry by a distance in metres.

    Auto-picks the correct UTM zone, buffers in metre-space, and
    reprojects back to WGS84 GeoJSON.
    """
    geom = parse(geojson)
    if distance_m < 0:
        raise ValueError("Buffer distance must be non-negative")
    result = units.buffer_in_meters(geom, distance_m, quad_segs)
    return serialize(result)


@safe_tool
def distance(geojson_a: str, geojson_b: str, unit: str = "m") -> float:
    """Geodesic centroid-to-centroid distance between two GeoJSON geometries."""
    geom_a = parse(geojson_a)
    geom_b = parse(geojson_b)
    return units.geodesic_distance(geom_a, geom_b, unit)


@safe_tool
def area(geojson: str, unit: str = "m2") -> float:
    """Geodesic area of a GeoJSON geometry on the WGS84 ellipsoid."""
    geom = parse(geojson)
    return units.geodesic_area(geom, unit)


@safe_tool
def length(geojson: str, unit: str = "m") -> float:
    """Geodesic length/perimeter of a GeoJSON geometry on the WGS84 ellipsoid."""
    geom = parse(geojson)
    return units.geodesic_length(geom, unit)


@safe_tool
def centroid(geojson: str) -> str:
    """Return the centroid of a GeoJSON geometry as a GeoJSON Point."""
    geom = parse(geojson)
    return serialize(geom.centroid)


@safe_tool
def simplify(geojson: str, tolerance: float, *, topology: bool = True) -> str:
    """Simplify a GeoJSON geometry using the Douglas-Peucker algorithm."""
    geom = parse(geojson)
    simplified = geom.simplify(tolerance, preserve_topology=topology)
    return serialize(simplified)


@safe_tool
def convex_hull(geojson: str) -> str:
    """Return the convex hull of a GeoJSON geometry."""
    geom = parse(geojson)
    return serialize(geom.convex_hull)


@safe_tool
def bbox(geojson: str) -> list[float]:
    """Return the bounding box [minx, miny, maxx, maxy] of a GeoJSON geometry."""
    geom = parse(geojson)
    b = geom.bounds
    return [b[0], b[1], b[2], b[3]]


_PREDICATE_OPS = {
    "intersects": lambda a, b: a.intersects(b),
    "within": lambda a, b: a.within(b),
    "contains": lambda a, b: a.contains(b),
    "touches": lambda a, b: a.touches(b),
    "overlaps": lambda a, b: a.overlaps(b),
    "crosses": lambda a, b: a.crosses(b),
    "disjoint": lambda a, b: a.disjoint(b),
    "equals": lambda a, b: a.equals(b),
}


@safe_tool
def spatial_predicate(geojson_a: str, geojson_b: str, op: str) -> bool:
    """Check a spatial relationship between two GeoJSON geometries.

    Supported operations: intersects, within, contains, touches, overlaps,
    crosses, disjoint, equals.
    """
    if op not in _PREDICATE_OPS:
        raise ValueError(f"Unknown spatial predicate: {op}. Supported: {list(_PREDICATE_OPS)}")
    geom_a = parse(geojson_a)
    geom_b = parse(geojson_b)
    return _PREDICATE_OPS[op](geom_a, geom_b)


@safe_tool
def transform_crs(geojson: str, from_crs: str, to_crs: str) -> str:
    """Reproject a GeoJSON geometry from one coordinate reference system to another.

    Uses EPSG codes (e.g., 'EPSG:4326', 'EPSG:3857') or PROJ strings.
    """
    geom = parse(geojson)
    result = units.reproject_geom(geom, from_crs, to_crs)
    return serialize(result)


@safe_tool
def validate_geojson(geojson: str) -> dict:
    """Validate a GeoJSON geometry and attempt repair if invalid.

    Returns: {valid, errors?, repaired}
    """
    try:
        geom = parse(geojson)
    except (ValueError, json.JSONDecodeError) as e:
        return {"valid": False, "errors": str(e)}

    valid = bool(geom.is_valid)
    if valid:
        return {"valid": True}

    explanation = explain_validity(geom)
    try:
        repaired = make_valid(geom)
        return {
            "valid": False,
            "errors": explanation,
            "repaired": serialize(repaired),
        }
    except Exception:
        return {"valid": False, "errors": explanation}
