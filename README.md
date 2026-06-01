# mcp-geo

A batteries-included geospatial server for the Model Context Protocol.  
It gives AI agents real access to geocoding, routing, OpenStreetMap querying,  
and spatial geometry operations — all returning clean GeoJSON.

[![PyPI version](https://img.shields.io/pypi/v/mcp-geo.svg)](https://pypi.org/project/mcp-geo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/tabibhasann/geo-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/tabibhasann/geo-mcp/actions/workflows/ci.yml)

## Quickstart

No configuration required — it runs out of the box with public OSM services.

```bash
pip install mcp-geo
```

Add it to your MCP client:

```json
{
  "mcpServers": {
    "geo": { "command": "uvx", "args": ["mcp-geo"] }
  }
}
```

That is it. Your AI agent now has 20+ geospatial tools available.

## Tools

**Local geometry (no network)**
`buffer` · `distance` · `area` · `length` · `centroid` · `simplify` · `convex_hull` · `bbox` · `spatial_predicate` · `transform_crs` · `validate_geojson`

**Geocoding & reverse geocoding (Nominatim)**
`geocode` · `reverse_geocode`

**OpenStreetMap querying (Overpass)**
`build_overpass_query` · `osm_features` · `overpass_query`

**Routing (OSRM)**
`route` · `route_matrix` · `nearest_road`

**File inspection (optional extras)**
`vector_info` · `vector_read` (`pip install mcp-geo[files]`)  
`raster_info` · `zonal_stats` · `sample_raster` (`pip install mcp-geo[raster]`)

All network tools respect rate limits and use a proper User-Agent header.

## Example: an agent answering a real spatial question

*"Find hospitals within 2 km of the Buriganga river in Dhaka"*

The agent composes four tools:
1. `geocode("Buriganga River, Dhaka")` → coordinates
2. `buffer(river, 2000)` → 2 km polygon
3. `osm_features(buffer, {"amenity": "hospital"})` → GeoJSON of hospitals
4. `distance` → sort by proximity

The agent handles the reasoning — mcp-geo handles the execution reliably.

## Configuration

Everything works without any setup. If you need to point at self-hosted
services (higher rate limits, air-gapped environments), set these environment
variables:

| Variable | Default |
|----------|---------|
| `GEO_MCP_NOMINATIM_URL` | `https://nominatim.openstreetmap.org` |
| `GEO_MCP_OSRM_URL` | `https://router.project-osrm.org` |
| `GEO_MCP_OVERPASS_URL` | `https://overpass-api.de/api/interpreter` |

Rate limiting is enforced client-side — **1 request per second** to Nominatim
by default. For production use, consider running your own Nominatim, OSRM,
and Overpass instances.

## Development

```bash
pip install -e ".[dev]"
ruff check src/ tests/
mypy src/
pytest --cov=geo_mcp tests/ -v
```

## License

MIT
