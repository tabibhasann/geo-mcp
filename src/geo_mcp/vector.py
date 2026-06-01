"""Vector file inspection tools (optional: requires pyogrio, geopandas)."""

from typing import Any

from .errors import safe_tool


def _check_files_deps() -> None:
    try:
        import geopandas  # noqa: F401
        import pyogrio  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Vector file support requires extra: [files]. "
            "Install with: pip install mcp-geo[files]"
        ) from e


@safe_tool
def vector_info(path: str) -> dict:
    """Get metadata about a vector file (Shapefile, GeoJSON, GeoPackage, etc.).

    Returns: {driver, crs, feature_count, geometry_types, fields, bbox, layers}.
    """
    _check_files_deps()
    import geopandas as gpd

    gdf = gpd.read_file(path)
    b = gdf.total_bounds

    return {
        "driver": None,  # pyogrio can't easily get driver post-read
        "crs": str(gdf.crs) if gdf.crs else None,
        "feature_count": len(gdf),
        "geometry_types": list(gdf.geom_type.unique()) if gdf.geom_type is not None else [],
        "fields": list(gdf.columns.drop("geometry", errors="ignore")),
        "field_types": {c: str(gdf[c].dtype) for c in gdf.columns if c != "geometry"},
        "bbox": [b[0], b[1], b[2], b[3]],
        "layers": None,
    }


@safe_tool
def vector_read(
    path: str,
    *,
    layer: str | None = None,
    limit: int = 500,
    bbox: str | None = None,
    where: str | None = None,
) -> dict:
    """Read features from a vector file as a GeoJSON FeatureCollection.

    Supports optional bounding box and attribute filters.
    """
    _check_files_deps()
    import geopandas as gpd
    from shapely import box

    kwargs = {}
    if layer:
        kwargs["layer"] = layer

    gdf = gpd.read_file(path, **kwargs)

    if bbox:
        import json as _json
        b = _json.loads(bbox) if isinstance(bbox, str) else bbox
        bbox_geom = box(b[0], b[1], b[2], b[3])
        gdf = gdf[gdf.geometry.intersects(bbox_geom)]

    if where:
        gdf = gdf.query(where)

    truncated = len(gdf) > limit
    gdf_out = gdf.head(limit)

    result: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [],
        "metadata": {
            "total_features": len(gdf),
            "returned": len(gdf_out),
        },
    }
    if truncated:
        result["metadata"]["truncated"] = True

    for _, row in gdf_out.iterrows():
        props = row.drop("geometry", errors="ignore").to_dict()
        for k, v in props.items():
            if hasattr(v, "item"):
                props[k] = v.item()

        _features = result["features"]  # type: ignore[assignment]
        _features.append({  # type: ignore[attr-defined]
            "type": "Feature",
            "id": len(_features),  # type: ignore[arg-type]
            "geometry": row.geometry.__geo_interface__,
            "properties": props,
        })

    return result
