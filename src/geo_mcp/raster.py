"""Raster file tools (optional: requires rasterio, rasterstats)."""

from .errors import safe_tool


def _check_raster_deps() -> None:
    try:
        import rasterio  # noqa: F401
        import rasterstats  # noqa: F401
    except ImportError as e:
        raise ImportError("Raster support requires extra: [raster]. Install with: pip install mcp-geo[raster]") from e


@safe_tool
def raster_info(path: str) -> dict:
    """Get metadata about a raster file.

    Returns: {crs, bands, width, height, bounds, res, nodata, dtype}.
    """
    _check_raster_deps()
    import rasterio

    with rasterio.open(path) as src:
        return {
            "crs": str(src.crs) if src.crs else None,
            "bands": src.count,
            "width": src.width,
            "height": src.height,
            "bounds": [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top],
            "res": (src.res[0], src.res[1]),
            "nodata": src.nodata,
            "dtype": str(src.dtypes[0]),
        }


@safe_tool
def zonal_stats(
    raster_path: str,
    zones_geojson: str,
    stats: list[str] | None = None,
) -> list[dict]:
    """Compute zonal statistics for polygon zones against a raster.

    stats: list of stat names, e.g. ["min", "max", "mean", "count"].
    Returns a list of dicts, one per zone.
    """
    _check_raster_deps()
    from rasterstats import zonal_stats as rzs

    if stats is None:
        stats = ["min", "max", "mean", "count"]

    import json as _json

    zones = _json.loads(zones_geojson) if isinstance(zones_geojson, str) else zones_geojson

    results = rzs(zones, raster_path, stats=stats, geojson_out=False)
    return list(results)


@safe_tool
def sample_raster(path: str, points_geojson: str) -> list[dict]:
    """Sample raster values at point locations.

    points_geojson: GeoJSON Point or MultiPoint geometry.
    Returns a list of point coordinates and sampled values.
    """
    _check_raster_deps()
    import json as _json

    import rasterio

    points = _json.loads(points_geojson) if isinstance(points_geojson, str) else points_geojson

    coords = []
    if points.get("type") == "Point":
        coords = [tuple(points["coordinates"])]
    elif points.get("type") == "MultiPoint":
        coords = [tuple(c) for c in points["coordinates"]]
    elif points.get("type") == "FeatureCollection":
        coords = [tuple(f["geometry"]["coordinates"]) for f in points["features"]]

    results = []
    with rasterio.open(path) as src:
        for x, y in coords:
            row, col = src.index(x, y)
            if 0 <= row < src.height and 0 <= col < src.width:
                values = [
                    float(src.read(i + 1, window=((row, row + 1), (col, col + 1)))[0, 0]) for i in range(src.count)
                ]
            else:
                values = None
            results.append({"lon": x, "lat": y, "values": values})

    return results
