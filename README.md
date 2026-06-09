# mcp-geo

A geospatial MCP server that gives agents dependable GIS tools: geocoding,
routing, OpenStreetMap queries, geometry operations, file inspection, raster
sampling, elevation, isochrones, static maps, and workspace storage.

[![PyPI version](https://img.shields.io/pypi/v/mcp-geo.svg)](https://pypi.org/project/mcp-geo/)
[![CI](https://github.com/tabibhasann/geo-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/tabibhasann/geo-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Why it exists

Geospatial work usually requires several specialized libraries and services.
`mcp-geo` packages common GIS operations behind stable MCP tools so an agent can
compose real spatial workflows instead of generating one-off scripts.

Example workflow:

1. `geocode` a place such as "Buriganga River, Dhaka".
2. `buffer` the returned point by 2 km.
3. `osm_features` for `{"amenity": "hospital"}` inside that area.
4. `distance` or `nearest_neighbor` to rank the results.
5. `static_map` or `save_map` to create a visual preview.

## Installation

```bash
pip install mcp-geo
```

For local GIS files:

```bash
pip install "mcp-geo[files,raster,visual]"
```

## MCP client config

```json
{
  "mcpServers": {
    "geo": {
      "command": "uvx",
      "args": ["mcp-geo"]
    }
  }
}
```

The default transport is stdio. HTTP and SSE are also available:

```bash
mcp-geo --http --host 127.0.0.1 --port 8000
mcp-geo --sse --host 127.0.0.1 --port 8000
```

## Tools

**Geometry**

`buffer`, `distance`, `area`, `length`, `centroid`, `simplify`, `convex_hull`,
`bbox`, `spatial_predicate`, `transform_crs`, `validate_geojson`

**Geocoding and OSM**

`geocode`, `reverse_geocode`, `build_overpass_query`, `osm_features`,
`overpass_query`

**Routing, elevation, and accessibility**

`route`, `route_matrix`, `nearest_road`, `elevation`, `elevation_profile`,
`isochrone`

**Files and rasters**

`vector_info`, `vector_read`, `raster_info`, `zonal_stats`, `sample_raster`

**Advanced workflows**

`build_spatial_index`, `spatial_query`, `spatial_join`, `cached_geocode`,
`batch_geocode`, `nearest_neighbor`, `repair_geometry`, `validate_geometry`

**Workspace and visualization**

`workspace_store`, `workspace_get`, `workspace_list`, `workspace_clear`,
`workspace_rename`, `static_map`, `save_map`, `suggest_tools`, `list_all_tools`

## Configuration

The server works without configuration by using public geospatial services.
For production use, self-host high-volume providers where possible.

| Variable | Default | Description |
| --- | --- | --- |
| `GEO_MCP_NOMINATIM_URL` | `https://nominatim.openstreetmap.org` | Forward and reverse geocoding |
| `GEO_MCP_OSRM_URL` | `https://router.project-osrm.org` | Routing and nearest-road lookup |
| `GEO_MCP_OVERPASS_URL` | `https://overpass-api.de/api/interpreter` | OpenStreetMap feature queries |
| `GEO_MCP_ORS_API_KEY` | unset | OpenRouteService key for isochrones |
| `GEO_MCP_HTTP_RETRIES` | `3` | HTTP retry count |

`mcp-geo` sends a project-specific User-Agent and rate-limits Nominatim calls to
one request per second by default.

## Development

```bash
git clone https://github.com/tabibhasann/geo-mcp.git
cd geo-mcp
uv sync --group dev
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest
```

Optional GIS dependencies can be tested with:

```bash
uv sync --group dev --extra files --extra raster --extra visual
uv run pytest
```

## Docker

```bash
docker build -t mcp-geo .
docker run --rm -p 8000:8000 mcp-geo mcp-geo --http --host 0.0.0.0 --port 8000
```

## License

MIT
