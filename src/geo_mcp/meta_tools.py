"""Tool discovery helpers for geospatial agents."""

from pydantic import BaseModel


class ToolSuggestion(BaseModel):
    """A suggested tool with a concise reason and example."""

    tool_name: str
    description: str
    use_case: str
    example: str


TOOL_CATALOG = {
    "geometry": {
        "buffer": {
            "description": "Create a metre-based buffer around a GeoJSON geometry",
            "use_case": "Build search areas such as all features within 2 km of a point",
            "example": "buffer(geojson=point_geojson, distance_m=2000)",
        },
        "distance": {
            "description": "Measure geodesic distance between two GeoJSON geometries",
            "use_case": "Rank candidates by proximity",
            "example": "distance(geojson_a=origin, geojson_b=destination, unit='km')",
        },
        "area": {
            "description": "Calculate geodesic area for a GeoJSON geometry",
            "use_case": "Measure parcels, service areas, flood zones, or administrative regions",
            "example": "area(geojson=polygon_geojson, unit='km2')",
        },
        "length": {
            "description": "Calculate geodesic length or perimeter",
            "use_case": "Measure roads, rivers, routes, and polygon perimeters",
            "example": "length(geojson=line_geojson, unit='km')",
        },
        "centroid": {
            "description": "Return the centroid of a GeoJSON geometry",
            "use_case": "Create a representative point for labels, routing, or sorting",
            "example": "centroid(geojson=polygon_geojson)",
        },
        "simplify": {
            "description": "Simplify geometry while preserving topology by default",
            "use_case": "Reduce payload size before visualization or API calls",
            "example": "simplify(geojson=large_polygon, tolerance=0.001)",
        },
        "convex_hull": {
            "description": "Return the convex hull of a geometry",
            "use_case": "Build a simple envelope around complex or scattered features",
            "example": "convex_hull(geojson=feature_geometry)",
        },
        "bbox": {
            "description": "Return a geometry bounding box",
            "use_case": "Convert results into bounds for Overpass or map previews",
            "example": "bbox(geojson=feature_geometry)",
        },
        "spatial_predicate": {
            "description": "Evaluate spatial relationships such as intersects, contains, or within",
            "use_case": "Filter features against boundaries or hazard zones",
            "example": "spatial_predicate(geojson_a=point, geojson_b=polygon, op='within')",
        },
        "transform_crs": {
            "description": "Reproject GeoJSON between coordinate reference systems",
            "use_case": "Move between WGS84 and projected CRS workflows",
            "example": "transform_crs(geojson=data, from_crs='EPSG:4326', to_crs='EPSG:3857')",
        },
        "validate_geojson": {
            "description": "Validate GeoJSON and return repair information when possible",
            "use_case": "Check user-provided geometry before analysis",
            "example": "validate_geojson(geojson=polygon_geojson)",
        },
    },
    "geocoding": {
        "geocode": {
            "description": "Convert a place name or address to coordinates",
            "use_case": "Start workflows from human-readable locations",
            "example": "geocode(query='Dhaka, Bangladesh', limit=1)",
        },
        "reverse_geocode": {
            "description": "Convert coordinates to a structured address",
            "use_case": "Explain map clicks or GPS coordinates",
            "example": "reverse_geocode(lat=23.8103, lon=90.4125)",
        },
    },
    "osm": {
        "build_overpass_query": {
            "description": "Build a safe Overpass QL query without executing it",
            "use_case": "Preview or debug OpenStreetMap queries",
            "example": "build_overpass_query(area=bbox, tags={'amenity': 'hospital'})",
        },
        "osm_features": {
            "description": "Query OpenStreetMap features and return GeoJSON",
            "use_case": "Find roads, hospitals, schools, parks, buildings, or amenities",
            "example": "osm_features(area='[23.7,90.3,23.9,90.5]', tags='{\"amenity\":\"hospital\"}')",
        },
        "overpass_query": {
            "description": "Execute raw Overpass QL and return GeoJSON",
            "use_case": "Run advanced OSM queries that exceed the safe builder",
            "example": "overpass_query(ql_string=query)",
        },
    },
    "routing": {
        "route": {
            "description": "Calculate a route between waypoints using OSRM",
            "use_case": "Estimate travel distance and duration",
            "example": "route(coordinates='[[90.41,23.81],[90.42,23.82]]', profile='driving')",
        },
        "route_matrix": {
            "description": "Build duration and distance matrices between points",
            "use_case": "Compare many origins and destinations",
            "example": "route_matrix(sources=origins_json, destinations=destinations_json)",
        },
        "nearest_road": {
            "description": "Snap a coordinate to the nearest road",
            "use_case": "Clean GPS points before routing",
            "example": "nearest_road(lat=23.8103, lon=90.4125)",
        },
        "isochrone": {
            "description": "Calculate reachable area from a point using OpenRouteService",
            "use_case": "Analyze service areas and accessibility",
            "example": "isochrone(lat=23.8103, lon=90.4125, range_value=600)",
        },
    },
    "elevation": {
        "elevation": {
            "description": "Get elevation at one coordinate",
            "use_case": "Add terrain context to a point",
            "example": "elevation(lat=23.8103, lon=90.4125)",
        },
        "elevation_profile": {
            "description": "Get elevation along a path",
            "use_case": "Analyze terrain changes along a route",
            "example": "elevation_profile(coordinates='[[90.41,23.81],[90.42,23.82]]')",
        },
    },
    "files": {
        "vector_info": {
            "description": "Inspect vector files such as GeoJSON, Shapefile, and GeoPackage",
            "use_case": "Understand file metadata before reading features",
            "example": "vector_info(path='data/roads.geojson')",
        },
        "vector_read": {
            "description": "Read vector file features as GeoJSON",
            "use_case": "Load local GIS files into an agent workflow",
            "example": "vector_read(path='data/roads.geojson', limit=100)",
        },
        "raster_info": {
            "description": "Inspect raster files such as GeoTIFF",
            "use_case": "Read CRS, bounds, bands, resolution, and nodata metadata",
            "example": "raster_info(path='data/dem.tif')",
        },
        "sample_raster": {
            "description": "Sample raster values at points",
            "use_case": "Fetch elevation, land cover, or other pixel values",
            "example": "sample_raster(path='data/dem.tif', points_geojson=points)",
        },
        "zonal_stats": {
            "description": "Summarize raster values inside polygon zones",
            "use_case": "Compute mean elevation, rainfall, or risk by area",
            "example": "zonal_stats(raster_path='data/dem.tif', zones_geojson=zones)",
        },
    },
    "advanced": {
        "build_spatial_index": {
            "description": "Build spatial-index metadata for a FeatureCollection",
            "use_case": "Check large collections before spatial queries",
            "example": "build_spatial_index(geojson_collection=features)",
        },
        "spatial_query": {
            "description": "Filter a FeatureCollection with a spatial predicate",
            "use_case": "Find features inside, touching, or intersecting an area",
            "example": "spatial_query(geojson_collection=features, query_geojson=polygon)",
        },
        "spatial_join": {
            "description": "Attach containing polygon IDs to point features",
            "use_case": "Assign schools, clinics, or survey points to zones",
            "example": "spatial_join(points_geojson=points, polygons_geojson=wards)",
        },
        "nearest_neighbor": {
            "description": "Find nearest features to a query geometry",
            "use_case": "Locate nearest hospitals, shelters, roads, or sensors",
            "example": "nearest_neighbor(query_geojson=point, candidates_geojson=features, k=3)",
        },
        "batch_geocode": {
            "description": "Geocode many addresses with in-process caching",
            "use_case": "Resolve CSV address lists or repeated place lookups",
            "example": "batch_geocode(addresses=['Dhaka', 'Chattogram'], limit=1)",
        },
        "cached_geocode": {
            "description": "Geocode one address through the in-process cache",
            "use_case": "Avoid repeated provider calls for common locations",
            "example": "cached_geocode(address='Dhaka, Bangladesh', limit=1)",
        },
        "repair_geometry": {
            "description": "Repair invalid polygon geometry when possible",
            "use_case": "Fix self-intersections before spatial joins or area calculations",
            "example": "repair_geometry(geojson=invalid_polygon)",
        },
        "validate_geometry": {
            "description": "Validate a geometry and explain geometry issues",
            "use_case": "Inspect invalid, empty, or self-intersecting shapes",
            "example": "validate_geometry(geojson=polygon_geojson)",
        },
    },
    "workspace": {
        "workspace_store": {
            "description": "Store intermediate JSON data by name",
            "use_case": "Reuse buffers, query results, or routes across tool calls",
            "example": "workspace_store(name='search_area', data=buffer_geojson)",
        },
        "workspace_get": {
            "description": "Retrieve a stored workspace item",
            "use_case": "Continue a multi-step spatial workflow",
            "example": "workspace_get(name='search_area')",
        },
        "workspace_list": {
            "description": "List stored workspace items",
            "use_case": "See available intermediate results",
            "example": "workspace_list()",
        },
        "workspace_clear": {
            "description": "Clear one workspace item or the entire workspace",
            "use_case": "Reset state between workflows",
            "example": "workspace_clear(name='search_area')",
        },
        "workspace_rename": {
            "description": "Rename a workspace item",
            "use_case": "Keep multi-step workflows readable",
            "example": "workspace_rename(old_name='tmp', new_name='service_area')",
        },
    },
    "visualization": {
        "static_map": {
            "description": "Render GeoJSON as a base64 PNG",
            "use_case": "Give users a quick map preview of spatial results",
            "example": "static_map(geojson=feature_collection)",
        },
        "save_map": {
            "description": "Render GeoJSON and save it as a PNG file",
            "use_case": "Create artifacts for reports or demos",
            "example": "save_map(geojson=feature_collection, output_path='map.png')",
        },
    },
}


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


def _make_suggestion(category: str, tool_name: str) -> ToolSuggestion:
    tool_info = TOOL_CATALOG[category][tool_name]
    return ToolSuggestion(
        tool_name=tool_name,
        description=tool_info["description"],
        use_case=tool_info["use_case"],
        example=tool_info["example"],
    )
