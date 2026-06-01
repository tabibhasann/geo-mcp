"""MCP server for mcp-geo. Registers 24 geospatial tools via FastMCP."""

from mcp.server.fastmcp import FastMCP

from . import geocoding, geometry, osm, raster, routing, vector

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

# Optional: vector
mcp.tool()(vector.vector_info)
mcp.tool()(vector.vector_read)

# Optional: raster
mcp.tool()(raster.raster_info)
mcp.tool()(raster.zonal_stats)
mcp.tool()(raster.sample_raster)


def main() -> None:
    """Run the MCP server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
