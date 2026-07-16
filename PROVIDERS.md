# Providers

mcp-geo uses a provider plugin system for geocoding, routing, and elevation.
Default providers are free and require no API key.

## Provider Capability Matrix

| Service | Provider | API Key | Config Variables | Tools Supported | Network/Privacy | Rate/Error Behavior | Fixture/Live-Test Status |
|---|---|---|---|---|---|---|---|
| Geocoding | Nominatim | No | `GEO_MCP_NOMINATIM_URL`, `GEO_MCP_NOMINATIM_DAILY_LIMIT` | `geocode`, `reverse_geocode`, `cached_geocode`, `batch_geocode` | Sends place names to public OSM server; User-Agent identifies the tool | 1 req/s rate-limited; retries on 5xx; quota tracker with 80%/100% thresholds | Fixture-tested via `respx` mocks; live test requires network |
| Routing | OSRM | No | `GEO_MCP_OSRM_URL`, `GEO_MCP_OSRM_DAILY_LIMIT` | `route`, `route_matrix`, `nearest_road` | Sends coordinates to public OSRM demo server | Retries on 5xx; quota tracker; demo server not for production | Fixture-tested via `respx` mocks; live test requires network |
| Elevation | Open-Elevation | No | `GEO_MCP_OPEN_ELEVATION_DAILY_LIMIT` | `elevation`, `elevation_profile` | Sends coordinates to public Open-Elevation API | Retries on 5xx; quota tracker; service may be intermittently unavailable | Fixture-tested via `unittest.mock`; live test requires network |
| Isochrones | OpenRouteService | Yes (`GEO_MCP_ORS_API_KEY`) | `GEO_MCP_ORS_URL`, `GEO_MCP_ORS_API_KEY` | `isochrone` | Sends coordinates to ORS API with API key | Raises clear error if key missing; retries on 5xx | Fixture-tested via `respx` mocks; requires API key for live use |
| OSM Features | Overpass API | No | `GEO_MCP_OVERPASS_URL` | `osm_features`, `overpass_query`, `build_overpass_query` | Sends Overpass QL to public Overpass API; query builder escapes user input | 30s timeout; retries on 5xx; large bbox auto-split into quadrants | Fixture-tested via `respx` mocks; live test requires network |
| Static Maps | matplotlib (local) | No | — | `static_map`, `save_map` | No network; renders locally with matplotlib | Fails clearly if `matplotlib` not installed (`pip install "mcp-geo[visual]"`) | Unit-tested locally |
| Vector Files | pyogrio/geopandas (local) | No | — | `vector_info`, `vector_read` | No network; reads local files | Fails clearly if `pyogrio` not installed (`pip install "mcp-geo[files]"`) | Unit-tested with in-memory fixtures |
| Raster Files | rasterio (local) | No | — | `raster_info`, `zonal_stats`, `sample_raster` | No network; reads local files | Fails clearly if `rasterio` not installed (`pip install "mcp-geo[raster]"`) | Unit-tested with in-memory fixtures |

### Privacy Notes

- All network-dependent providers send geospatial queries to public free-tier services.
- No telemetry, analytics, or usage tracking is sent by mcp-geo itself.
- The `--dry-run` flag returns mock data without any network calls.
- Local-only tools (geometry, workspace, static maps, vector/raster I/O) make zero network requests.
- Self-hosting: set `GEO_MCP_NOMINATIM_URL`, `GEO_MCP_OSRM_URL`, and `GEO_MCP_OVERPASS_URL` to your own instances for complete data sovereignty.

## Selecting a Provider

Set environment variables to choose which provider handles each service:

```bash
export GEO_MCP_GEOCODING_PROVIDER=nominatim   # default
export GEO_MCP_ROUTING_PROVIDER=osrm           # default
export GEO_MCP_ELEVATION_PROVIDER=open_elevation  # default
```

## Adding a Custom Provider

1. Subclass the relevant ABC from `geo_mcp.providers`:

```python
from geo_mcp.providers import GeocodingProvider

class MapboxGeocoding(GeocodingProvider):
    async def geocode(self, query, *, limit, countrycodes):
        # Call Mapbox Geocoding API
        ...

    async def reverse_geocode(self, lat, lon, *, zoom):
        # Call Mapbox Reverse Geocoding API
        ...
```

2. Register it in `PROVIDER_REGISTRY`:

```python
PROVIDER_REGISTRY["geocoding"]["mapbox"] = MapboxGeocoding
```

3. Set the environment variable:

```bash
export GEO_MCP_GEOCODING_PROVIDER=mapbox
```

## Quota Tracking

Set daily limits to track API usage:

```bash
export GEO_MCP_NOMINATIM_DAILY_LIMIT=1000
export GEO_MCP_OSRM_DAILY_LIMIT=5000
```

When usage reaches 80%, a warning is printed to stderr.
When usage reaches 100%, a `RuntimeError` is raised.

## Dry-Run Mode

Use `--dry-run` to return mock data without hitting any API:

```bash
mcp-geo --dry-run
```

Or set the environment variable:

```bash
export GEO_MCP_DRY_RUN=true
```
