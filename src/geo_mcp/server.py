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
    parser.add_argument("--dry-run", action="store_true", help="Return mock data without hitting APIs.")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress/warning output (CI mode).")
    parser.add_argument("--version", action="version", version=f"mcp-geo {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="Check API connectivity and configuration.")
    sub.add_parser("tools", help="List all available tools with descriptions.")
    sub.add_parser("providers", help="List configured providers.")
    return parser


async def _doctor() -> None:
    """Run connectivity checks against configured providers."""
    import httpx

    from .config import settings

    checks = [
        ("Nominatim (geocoding)", settings.nominatim_url, "/search?q=test&format=json&limit=1"),
        ("OSRM (routing)", settings.osrm_url, "/route/v1/driving/0,0;0.001,0.001?overview=false"),
        ("Overpass (OSM queries)", settings.overpass_url, ""),
    ]
    if settings.ors_api_key:
        checks.append(("OpenRouteService (isochrones)", settings.ors_url, "/v2/health"))

    print(f"mcp-geo {__version__} — doctor\n")
    all_ok = True
    async with httpx.AsyncClient(
        headers={"User-Agent": settings.user_agent},
        timeout=httpx.Timeout(10.0),
    ) as client:
        for name, base, path in checks:
            url = f"{base}{path}" if path else base
            try:
                resp = await client.get(url)
                status = resp.status_code
                ok = status < 500
                symbol = "✓" if ok else "✗"
                print(f"  {symbol} {name}: HTTP {status}")
                if not ok:
                    all_ok = False
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                all_ok = False

    print(f"\n  ORS API key: {'set' if settings.ors_api_key else 'not set (isochrones disabled)'}")
    print(f"  Rate limit:  {settings.nominatim_rate_limit} req/s (Nominatim)")
    print(f"  Retries:     {settings.http_retries}")
    print(f"\n  {'All checks passed.' if all_ok else 'Some providers unreachable — check network/config.'}")
    raise SystemExit(0 if all_ok else 1)


def _tools() -> None:
    """List all available tools with descriptions."""
    from .meta_tools import TOOL_CATALOG

    total = sum(len(tools) for tools in TOOL_CATALOG.values())
    print(f"mcp-geo {__version__} — {total} tools\n")
    for category, tools in TOOL_CATALOG.items():
        print(f"  {category} ({len(tools)}):")
        for name, info in tools.items():
            print(f"    {name:24s}  {info['description']}")
        print()


def _providers() -> None:
    """List configured providers."""
    from .providers import list_providers

    registry = list_providers()
    print(f"mcp-geo {__version__} — providers\n")
    for service, providers in registry.items():
        active = getattr(__import__("geo_mcp.config", fromlist=["settings"]).settings, f"{service}_provider", "default")
        print(f"  {service}:")
        for name, info in providers.items():
            marker = " *" if name == active else ""
            print(f"    {name}{marker}  ({info['class']})")
        print()


def main() -> None:
    """Run the MCP server."""
    args = _parser().parse_args(sys.argv[1:])

    if args.command == "doctor":
        import asyncio

        asyncio.run(_doctor())
        return

    if args.command == "tools":
        _tools()
        return

    if args.command == "providers":
        _providers()
        return

    from .config import settings

    if args.dry_run:
        settings.dry_run = True
    if args.quiet:
        settings.quiet = True

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
