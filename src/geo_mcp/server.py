"""MCP server for mcp-geo. Registers 44 geospatial tools via FastMCP."""

import argparse
import sys

from mcp.server.fastmcp import FastMCP

from . import (
    __version__,
    advanced,
    elevation,
    geocoding,
    geometry,
    isochrones,
    meta_tools,
    osm,
    raster,
    routing,
    static_map,
    vector,
    workspace,
)

mcp = FastMCP("mcp-geo")

# Geometry
mcp.tool()(geometry.buffer)
mcp.tool()(geometry.distance)
mcp.tool()(geometry.area)
mcp.tool()(geometry.length)
mcp.tool()(geometry.centroid)
mcp.tool()(geometry.simplify)
mcp.tool()(geometry.convex_hull)
mcp.tool()(geometry.bbox)
mcp.tool()(geometry.spatial_predicate)
mcp.tool()(geometry.transform_crs)
mcp.tool()(geometry.validate_geojson)

# Geocoding
mcp.tool()(geocoding.geocode)
mcp.tool()(geocoding.reverse_geocode)

# OSM / Overpass
mcp.tool()(osm.build_overpass_query)
mcp.tool()(osm.osm_features)
mcp.tool()(osm.overpass_query)

# Routing
mcp.tool()(routing.route)
mcp.tool()(routing.route_matrix)
mcp.tool()(routing.nearest_road)

# Elevation
mcp.tool()(elevation.elevation)
mcp.tool()(elevation.elevation_profile)

# Isochrones
mcp.tool()(isochrones.isochrone)

# Optional: vector
mcp.tool()(vector.vector_info)
mcp.tool()(vector.vector_read)

# Optional: raster
mcp.tool()(raster.raster_info)
mcp.tool()(raster.zonal_stats)
mcp.tool()(raster.sample_raster)

# Advanced spatial tools
mcp.tool()(advanced.build_spatial_index)
mcp.tool()(advanced.spatial_query)
mcp.tool()(advanced.spatial_join)
mcp.tool()(advanced.cached_geocode)
mcp.tool()(advanced.batch_geocode)
mcp.tool()(advanced.nearest_neighbor)
mcp.tool()(advanced.repair_geometry)
mcp.tool()(advanced.validate_geometry)

# Static map visualization
mcp.tool()(static_map.static_map)
mcp.tool()(static_map.save_map)

# Workspace storage
mcp.tool()(workspace.workspace_store)
mcp.tool()(workspace.workspace_get)
mcp.tool()(workspace.workspace_list)
mcp.tool()(workspace.workspace_clear)
mcp.tool()(workspace.workspace_rename)

# Meta-tools for agent discovery
mcp.tool()(meta_tools.suggest_tools)
mcp.tool()(meta_tools.list_all_tools)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the mcp-geo server.")
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument("--stdio", action="store_true", help="Run stdio transport (default).")
    transport.add_argument("--sse", action="store_true", help="Run Server-Sent Events transport.")
    transport.add_argument("--http", "--streamable-http", action="store_true", help="Run streamable HTTP transport.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP/SSE transports.")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP/SSE transports.")
    parser.add_argument("--version", action="version", version=f"mcp-geo {__version__}")
    return parser


def main() -> None:
    """Run the MCP server."""
    args = _parser().parse_args(sys.argv[1:])
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    if args.sse:
        mcp.run(transport="sse")
    elif args.http:
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
