"""Static map rendering for quick visual feedback."""

import base64
import contextlib
import io
import json
from pathlib import Path
from typing import Any

from .errors import safe_tool


def _extract_geometries(data: dict[str, Any]) -> list[Any]:
    from shapely.geometry import shape

    geometries = []
    if data.get("type") == "FeatureCollection":
        for feature in data.get("features", []):
            geometry = feature.get("geometry")
            if geometry:
                with contextlib.suppress(Exception):
                    geometries.append(shape(geometry))
    elif data.get("type") == "Feature":
        geometry = data.get("geometry")
        if geometry:
            with contextlib.suppress(Exception):
                geometries.append(shape(geometry))
    else:
        with contextlib.suppress(Exception):
            geometries.append(shape(data))
    return geometries


def _auto_zoom(bounds: tuple[float, float, float, float]) -> int:
    min_lon, min_lat, max_lon, max_lat = bounds
    max_range = max(max_lon - min_lon, max_lat - min_lat)
    thresholds = [
        (180, 1),
        (90, 2),
        (45, 3),
        (22, 4),
        (11, 5),
        (5, 6),
        (2, 8),
        (1, 9),
        (0.5, 10),
        (0.1, 12),
        (0.05, 13),
        (0.01, 15),
    ]
    for size, zoom in thresholds:
        if max_range > size:
            return zoom
    return 16


def _style_colors(style: str) -> tuple[str, str, str, str]:
    if style == "carto-dark":
        return "#2b2b2b", "#00d4ff", "#00a8cc", "white"
    if style == "osm":
        return "#f2efe9", "#ff6b6b", "#c92a2a", "black"
    return "#f8f4f0", "#4a90e2", "#357abd", "black"


@safe_tool
def static_map(
    geojson: str,
    width: int = 800,
    height: int = 600,
    style: str = "carto-light",
    zoom: int | None = None,
    center: list[float] | None = None,
) -> dict:
    """Render GeoJSON as a base64-encoded PNG."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from shapely.ops import unary_union
    except ImportError as e:
        raise ImportError("Static maps require matplotlib") from e

    data = json.loads(geojson)
    geometries = _extract_geometries(data)
    if not geometries:
        raise ValueError("No valid geometries found in GeoJSON")

    all_geoms = unary_union(geometries)
    bounds = all_geoms.bounds
    min_lon, min_lat, max_lon, max_lat = bounds
    center_lon, center_lat = center or [(min_lon + max_lon) / 2, (min_lat + max_lat) / 2]
    zoom = zoom if zoom is not None else _auto_zoom(bounds)

    background, fill_color, edge_color, text_color = _style_colors(style)
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    fig.patch.set_facecolor(background)
    ax.set_facecolor(background)

    for geom in geometries:
        if geom.geom_type == "Point":
            ax.plot(geom.x, geom.y, "o", color=fill_color, markersize=8, markeredgecolor=edge_color)
        elif geom.geom_type == "MultiPoint":
            for point in geom.geoms:
                ax.plot(point.x, point.y, "o", color=fill_color, markersize=8, markeredgecolor=edge_color)
        elif geom.geom_type == "LineString":
            x, y = geom.xy
            ax.plot(x, y, "-", color=fill_color, linewidth=2)
        elif geom.geom_type == "MultiLineString":
            for line in geom.geoms:
                x, y = line.xy
                ax.plot(x, y, "-", color=fill_color, linewidth=2)
        elif geom.geom_type == "Polygon":
            x, y = geom.exterior.xy
            ax.fill(x, y, color=fill_color, alpha=0.3, edgecolor=edge_color, linewidth=1.5)
        elif geom.geom_type == "MultiPolygon":
            for polygon in geom.geoms:
                x, y = polygon.exterior.xy
                ax.fill(x, y, color=fill_color, alpha=0.3, edgecolor=edge_color, linewidth=1.5)

    lon_padding = max((max_lon - min_lon) * 0.1, 0.001)
    lat_padding = max((max_lat - min_lat) * 0.1, 0.001)
    if center:
        ax.set_xlim(center_lon - lon_padding * 2, center_lon + lon_padding * 2)
        ax.set_ylim(center_lat - lat_padding * 2, center_lat + lat_padding * 2)
    else:
        ax.set_xlim(min_lon - lon_padding, max_lon + lon_padding)
        ax.set_ylim(min_lat - lat_padding, max_lat + lat_padding)

    ax.grid(True, alpha=0.2, color="gray")
    ax.set_xlabel("Longitude", color=text_color, fontsize=10)
    ax.set_ylabel("Latitude", color=text_color, fontsize=10)
    ax.tick_params(colors=text_color, labelsize=8)
    ax.set_title(f"Static Map (zoom: {zoom}, {len(geometries)} features)", color=text_color, fontsize=12, pad=10)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)

    return {
        "image_base64": image_base64,
        "width": width,
        "height": height,
        "bounds": [min_lon, min_lat, max_lon, max_lat],
        "center": [center_lon, center_lat],
        "zoom": zoom,
        "feature_count": len(geometries),
    }


@safe_tool
def save_map(
    geojson: str,
    output_path: str,
    width: int = 800,
    height: int = 600,
    style: str = "carto-light",
) -> dict:
    """Render GeoJSON and save it as a PNG file."""
    result = static_map(geojson, width=width, height=height, style=style)
    if "error" in result:
        return result

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(base64.b64decode(result["image_base64"]))

    return {
        "success": True,
        "path": str(target),
        "width": result["width"],
        "height": result["height"],
        "bounds": result["bounds"],
        "center": result["center"],
        "zoom": result["zoom"],
        "feature_count": result["feature_count"],
    }
