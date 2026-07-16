# mcp-geo

> **Release status:** PyPI currently provides v0.3.0. This checkout is the v0.4.0 release candidate and must be released before users receive its newest provider and hardening work.

A geospatial MCP server that gives agents dependable GIS tools: geocoding,
routing, OpenStreetMap queries, geometry operations, file inspection, raster
sampling, elevation, isochrones, static maps, and workspace storage.

[![PyPI version](https://img.shields.io/pypi/v/mcp-geo.svg)](https://pypi.org/project/mcp-geo/)
[![CI](https://github.com/tabibhasann/geo-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/tabibhasann/geo-mcp/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-76%25-brightgreen)](https://github.com/tabibhasann/geo-mcp/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)


**Demo:** Run the MCP examples below. A hosted tool gallery is pending.

```
                          +-------------------+
   Natural-language       |     mcp-geo       |    Deterministic
   agent request   -----> |  44 MCP tools     | --->  geospatial results
   (Claude, Cursor, ...)  |  12 categories    |      + rendered maps
                          +-------------------+
```

## Why it exists

Geospatial work usually requires several specialized libraries and services.
`mcp-geo` packages common GIS operations behind stable MCP tools so an agent can
compose real spatial workflows instead of generating one-off scripts.

### How it compares

| Tool | Tools count | Geocoding | Routing | OSM | Elevation | Isochrones | Raster | Static maps | File I/O | Self-hostable |
|---|---|---|---|---|---|---|---|---|---|---|
| **mcp-geo** | 44 | ✅ Nominatim | ✅ OSRM | ✅ Overpass | ✅ Open-Elevation | ✅ ORS | ✅ rasterio | ✅ matplotlib | ✅ pyogrio | ✅ all providers |
| [gis-mcp](https://github.com/aliyun2021/gis-mcp) | ~15 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | partial |
| [CARTO MCP](https://carto.com/blog/carto-mcp-server/) | ~10 | ✅ CARTO | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ SaaS only |
| [Felt MCP](https://felt.com/blog/mcp) | ~8 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ SaaS only |

mcp-geo offers a broad open-source GIS tool surface — from geocoding to raster
sampling to static map rendering — in a single package. Its core providers do not
require API keys, and the server can be self-hosted.

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

Check provider connectivity and configuration:

```bash
mcp-geo doctor
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

## Example: MCP tool call

```json
// Agent calls: geocode("Brandenburg Gate, Berlin")
// Server returns:
[
  {
    "lat": 52.5163,
    "lon": 13.3777,
    "display_name": "Brandenburg Gate, Berlin, Germany",
    "type": "tourism",
    "importance": 0.8
  }
]

// Agent chains: buffer(point, distance_m=1000)
// Server returns:
{
  "type": "Polygon",
  "coordinates": [[[13.3689, 52.5074], ...]]
}
```

## Examples

End-to-end workflows and example agent prompts are in
[EXAMPLES.md](EXAMPLES.md). Highlights:

- Hospital search around the Buriganga river
- 15-minute drive-time isochrone + restaurant search
- Elevation profile for a hike
- Local GeoPackage inspection
- Raster sampling and zonal stats
- Accelerated spatial queries over large collections

## Service usage policies

The default providers are free public services with usage policies:

- **Nominatim**: Max 1 request/second, requires a valid User-Agent. See [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/).
- **OSRM**: Free demo server, not for production. Self-host for heavy use.
- **Overpass**: Fair use, avoid large queries during peak hours.

For production, self-host these services or use commercial providers (Mapbox, Google, OpenRouteService).

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

## Alternatives

| Tool | Type | Scope | MCP-native | Python | npm |
|------|------|-------|-----------|--------|-----|
| **mcp-geo** | MCP server | 44 GIS tools (geometry, geocoding, routing, raster, etc.) | Yes | Yes | No |
| [geo-mcp-server](https://github.com/nicholishen/geo-mcp-server) | MCP server | Focused on geocoding + maps | Yes | No | Yes |
| [QGIS](https://qgis.org) | Desktop GIS | Full desktop GIS suite | No | Plugin API | No |
| [geopandas](https://geopandas.org) | Python library | DataFrame-style geospatial ops | No | Yes | No |
| [shapely](https://shapely.readthedocs.io) | Python library | Low-level geometry ops | No | Yes | No |

**Why mcp-geo?** It bundles the most common GIS operations (44 tools across 12 categories) behind a single MCP server so any agent can perform spatial analysis without custom integrations per tool.

## Roadmap

**What works now:**
- 44 MCP tools across 12 categories (geometry, geocoding, OSM, routing, elevation, isochrones, files, raster, spatial index, workspace, visualization, meta-tools)
- stdio, HTTP, and SSE transports
- Rate limiting and retry logic for public APIs
- `mcp-geo doctor` connectivity checker
- `--dry-run` mode (returns mock data without hitting APIs)
- `--quiet` flag for CI (suppresses progress output)
- Quota tracking with 80% warning and 100% error thresholds
- `mcp-geo tools` command for tool discovery
- `mcp-geo providers` command for provider listing

**Planned:**
- Provider plugin system (Mapbox, Google Maps geocoding)
- WebSockets transport
- Batch file processing tools
- More raster operations (reproject, clip, mosaic)

## Quick Start

```bash
# Install
pip install mcp-geo

# Run as MCP server (add to your agent's MCP config)
mcp-geo

# List all available tools
mcp-geo tools

# List configured providers
mcp-geo providers
```

### Agent Configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "geo": {
      "command": "mcp-geo",
      "env": {
        "NOMINATIM_EMAIL": "you@example.com",
        "OPENTRIPMAP_KEY": "optional"
      }
    }
  }
}
```

## API

### MCP Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| Geocoding | 4 | Forward/reverse geocoding via Nominatim |
| Routing | 3 | Route planning via OSRM |
| OSM | 5 | OpenStreetMap queries (POI, isochrones, static maps) |
| Geometry | 6 | Buffer, intersect, distance, area, centroid, transform |
| Files | 5 | Inspect GeoJSON, Shapefile, GeoPackage, KML, CSV |
| Raster | 4 | Sample, stats, contour, reproject |
| Elevation | 3 | Point, profile, batch elevation |
| Workspace | 4 | Save/retrieve spatial data between tool calls |

### Python API

```python
from geo_mcp.server import mcp

# Run the MCP server
mcp.run()
```


## CLI Reference

\`\`\`bash
geo-mcp --help     # Show all available commands and options
geo-mcp --version  # Print the installed version
\`\`\`

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT

---

⭐ Star [tabibhasann/geo-mcp](https://github.com/tabibhasann/geo-mcp) on GitHub if this helped you.
