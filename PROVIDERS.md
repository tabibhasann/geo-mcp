# Providers

mcp-geo uses a provider plugin system for geocoding, routing, and elevation.
Default providers are free and require no API key.

## Default Providers

| Service     | Provider         | API Key | URL                                      |
|-------------|------------------|---------|------------------------------------------|
| Geocoding   | Nominatim        | No      | https://nominatim.openstreetmap.org      |
| Routing     | OSRM             | No      | https://router.project-osrm.org          |
| Elevation   | Open-Elevation   | No      | https://api.open-elevation.com           |
| Isochrones  | OpenRouteService | Yes     | https://api.openrouteservice.org         |

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
