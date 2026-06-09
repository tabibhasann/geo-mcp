"""Unit conversions, geodesic calculations, and UTM zone picking."""

import json
from typing import Any

from pyproj import Geod, Transformer
from shapely import from_geojson, to_geojson
from shapely.geometry import mapping

WGS84_GEOD = Geod(ellps="WGS84")


def parse_geojson(geojson_str: str) -> dict[str, Any]:
    """Parse a GeoJSON string into a Python dict."""
    try:
        return json.loads(geojson_str) if isinstance(geojson_str, str) else geojson_str
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid GeoJSON: {e}") from e


def geojson_to_shapely(geojson_str: str):
    """Convert GeoJSON string to a shapely geometry object."""
    data = parse_geojson(geojson_str)
    geom_data = data.get("geometry", data)
    return from_geojson(json.dumps(geom_data))


def shapely_to_geojson(geom, indent: int | None = None) -> str:
    """Convert a shapely geometry to a GeoJSON string."""
    return json.dumps(mapping(geom), indent=indent)


def get_centroid_lonlat(geom) -> tuple[float, float]:
    """Get (lon, lat) of geometry centroid in WGS84."""
    centroid = geom.centroid
    return (centroid.x, centroid.y)


def pick_utm_epsg(geom) -> str:
    """Auto-compute the UTM EPSG code for the geometry centroid.

    Returns EPSG:326xx for northern hemisphere, 327xx for southern.
    """
    lon, lat = get_centroid_lonlat(geom)
    utm_zone = int((lon + 180) / 6) + 1
    utm_zone = max(1, min(60, utm_zone))
    if lat >= 0:
        return f"EPSG:326{utm_zone:02d}"
    return f"EPSG:327{utm_zone:02d}"


def geodesic_area(geom, unit: str = "m2") -> float:
    """Compute geodesic area of a geometry on the WGS84 ellipsoid.

    Works by projecting to a local azimuthal equal-area projection,
    computing planar area, and converting units.
    """
    try:
        area_m2, _ = WGS84_GEOD.geometry_area_perimeter(geom)
        return abs(convert_area(area_m2, "m2", unit))
    except Exception:
        # fallback: reproject to equal area
        lon, lat = get_centroid_lonlat(geom)
        crs_str = f"+proj=laea +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
        transformer = Transformer.from_crs("EPSG:4326", crs_str, always_xy=True)
        geom_json = json.loads(to_geojson(geom))
        _transform_coords(geom_json, transformer)
        geom_proj = from_geojson(json.dumps(geom_json))
        area_m2 = geom_proj.area
        return convert_area(area_m2, "m2", unit)


def geodesic_length(geom, unit: str = "m") -> float:
    """Compute geodesic length/perimeter on the WGS84 ellipsoid."""
    try:
        _, perimeter_m = WGS84_GEOD.geometry_area_perimeter(geom)
        return convert_length(perimeter_m, "m", unit)
    except Exception:
        length_m = WGS84_GEOD.geometry_length(geom)
        return convert_length(length_m, "m", unit)


def reproject_geom(geom, from_crs: str, to_crs: str):
    """Reproject a shapely geometry between CRS using pyproj's geometry transform."""
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    geom_json = json.loads(to_geojson(geom))
    _transform_coords(geom_json, transformer)
    return from_geojson(json.dumps(geom_json))


def _transform_coords(geom_data: dict, transformer) -> None:
    """Recursively transform coordinates in a GeoJSON-like dict."""
    if geom_data.get("type") == "Point":
        x, y = geom_data["coordinates"]
        geom_data["coordinates"] = list(transformer.transform(x, y))  # pyproj 3.6+ signature
    elif geom_data.get("type") in ("LineString", "MultiPoint"):
        for i, (x, y) in enumerate(geom_data["coordinates"]):
            geom_data["coordinates"][i] = list(transformer.transform(x, y))
    elif geom_data.get("type") == "Polygon":
        for ring in geom_data["coordinates"]:
            for i, (x, y) in enumerate(ring):
                ring[i] = list(transformer.transform(x, y))
    elif geom_data.get("type") == "MultiPolygon":
        for poly in geom_data["coordinates"]:
            for ring in poly:
                for i, (x, y) in enumerate(ring):
                    ring[i] = list(transformer.transform(x, y))
    elif geom_data.get("type") == "MultiLineString":
        for line in geom_data["coordinates"]:
            for i, (x, y) in enumerate(line):
                line[i] = list(transformer.transform(x, y))
    elif geom_data.get("type") == "GeometryCollection":
        for g in geom_data.get("geometries", []):
            _transform_coords(g, transformer)


def buffer_in_meters(geom, distance_m: float, quad_segs: int = 8):
    """Buffer a WGS84 geometry by a distance in metres.

    Reprojects to the appropriate UTM zone, buffers in metres, then
    reprojects back to EPSG:4326.
    """
    utm = pick_utm_epsg(geom)
    geom_utm = reproject_geom(geom, "EPSG:4326", utm)
    buffered = geom_utm.buffer(distance_m, quad_segs=quad_segs)
    return reproject_geom(buffered, utm, "EPSG:4326")


def geodesic_distance(geom_a, geom_b, unit: str = "m") -> float:
    """Compute geodesic distance between two geometry centroids."""
    ax, ay = get_centroid_lonlat(geom_a)
    bx, by = get_centroid_lonlat(geom_b)
    _, _, dist_m = WGS84_GEOD.inv(ax, ay, bx, by)
    return convert_length(dist_m, "m", unit)


_UNIT_MAP = {
    "m": 1.0,
    "km": 0.001,
    "mi": 0.000621371,
    "ft": 3.28084,
}

_AREA_UNIT_MAP = {
    "m2": 1.0,
    "km2": 1e-6,
    "ha": 1e-4,
    "mi2": 3.861e-7,
    "ft2": 10.7639,
    "acre": 0.000247105,
}


def convert_length(value_m: float, from_unit: str, to_unit: str) -> float:
    """Convert a length from one unit to another (metre-based)."""
    factor = _UNIT_MAP.get(to_unit)
    if factor is None:
        raise ValueError(f"Unknown length unit: {to_unit}. Supported: {list(_UNIT_MAP)}")
    return value_m * factor


def convert_area(value_m2: float, from_unit: str, to_unit: str) -> float:
    """Convert an area from one unit to another (m²-based)."""
    factor = _AREA_UNIT_MAP.get(to_unit)
    if factor is None:
        raise ValueError(f"Unknown area unit: {to_unit}. Supported: {list(_AREA_UNIT_MAP)}")
    return value_m2 * factor
