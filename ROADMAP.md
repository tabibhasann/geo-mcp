# Roadmap

## v0.3 (released)
- [x] Isochrones via OpenRouteService
- [x] Elevation lookup (Open-Elevation API)
- [x] Elevation profile along paths
- [x] HTTP/SSE transport mode for remote server use
- [x] Docker image for self-hosting
- [x] Input validation on all coordinate parameters
- [x] HTTP retry logic for resilience
- [x] Fixed vector_info driver detection via pyogrio

## v0.4 (next)
- MBTiles and PMTiles metadata inspection
- GeoParquet read/write helpers
- Provider plugin system for swappable geocoding, routing, and elevation backends
- Safer Overpass query budgeting for very large areas
- Example notebooks for disaster response, healthcare access, and urban planning

## v0.5
- Typed tool schemas with richer examples for MCP clients
- Optional PostGIS import/export helpers
- Better CRS detection and warnings for local files
- Map artifact gallery for documentation

## v1.0
- Stable public tool contracts
- Provider plugin system for swappable backends
- Comprehensive test coverage (90%+)
- Security and performance audit for public-service defaults
