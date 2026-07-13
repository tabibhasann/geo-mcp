"""Tool discovery and suggestion logic for geospatial agents."""

from __future__ import annotations

from .catalog import TOOL_CATALOG, _make_suggestion


def suggest_tools(task_description: str, context: str | None = None) -> dict:
    """Suggest relevant tools for a natural-language geospatial task."""
    task_lower = f"{task_description} {context or ''}".lower()
    suggested = []
    workflow_steps = []

    if any(word in task_lower for word in ["address", "place", "city", "location", "near"]) or " of " in task_lower:
        suggested.append(_make_suggestion("geocoding", "geocode"))
        workflow_steps.append("Resolve place names with geocode.")
    if any(word in task_lower for word in ["hospital", "school", "park", "road", "building", "amenity"]):
        suggested.append(_make_suggestion("osm", "osm_features"))
        workflow_steps.append("Query OpenStreetMap with osm_features.")
    if any(word in task_lower for word in ["near", "within", "around", "radius", "km", "mile"]):
        suggested.append(_make_suggestion("geometry", "buffer"))
        suggested.append(_make_suggestion("geometry", "distance"))
        workflow_steps.append("Create a search area with buffer, then rank with distance.")
    if any(word in task_lower for word in ["route", "drive", "walk", "cycling", "travel"]):
        suggested.append(_make_suggestion("routing", "route"))
        workflow_steps.append("Calculate travel paths with route.")
    if any(word in task_lower for word in ["accessible", "service area", "reachable", "isochrone"]):
        suggested.append(_make_suggestion("routing", "isochrone"))
        workflow_steps.append("Use isochrone for reachable-area analysis.")
    if any(word in task_lower for word in ["raster", "tif", "tiff", "dem", "elevation model"]):
        suggested.append(_make_suggestion("files", "raster_info"))
        suggested.append(_make_suggestion("files", "zonal_stats"))
    if any(word in task_lower for word in ["shapefile", "geojson", "geopackage", "vector"]):
        suggested.append(_make_suggestion("files", "vector_info"))
        suggested.append(_make_suggestion("files", "vector_read"))
    if any(word in task_lower for word in ["join", "zone", "contains", "within"]):
        suggested.append(_make_suggestion("advanced", "spatial_join"))
        suggested.append(_make_suggestion("advanced", "spatial_query"))
    if any(word in task_lower for word in ["nearest", "closest"]):
        suggested.append(_make_suggestion("advanced", "nearest_neighbor"))
    if any(word in task_lower for word in ["map", "visualize", "preview", "png"]):
        suggested.append(_make_suggestion("visualization", "static_map"))

    if not workflow_steps:
        workflow_steps = [
            "Start with geocode, vector_read, or osm_features to collect spatial inputs.",
            "Use geometry or advanced tools to analyze relationships.",
            "Use static_map when a visual preview helps explain the result.",
        ]

    unique_suggested = []
    seen = set()
    for suggestion in suggested:
        if suggestion.tool_name not in seen:
            seen.add(suggestion.tool_name)
            unique_suggested.append(suggestion)

    return {
        "suggested_tools": [suggestion.model_dump() for suggestion in unique_suggested],
        "workflow_hint": " ".join(workflow_steps),
        "total_tools_available": sum(len(tools) for tools in TOOL_CATALOG.values()),
    }


def list_all_tools() -> dict:
    """Return the full tool catalog grouped by category."""
    return {
        "categories": TOOL_CATALOG,
        "total_tools": sum(len(tools) for tools in TOOL_CATALOG.values()),
    }
