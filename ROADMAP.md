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

## v0.4 (release candidate)
- [x] Provider plugin system for swappable geocoding, routing, and elevation backends
- [x] Expanded tool surface and provider-resilience tests
- [x] Provider capability matrix in PROVIDERS.md
- [x] Fixture-based provider contract tests (22 tests covering all providers)
- [x] Three copy-paste end-to-end GIS workflows in EXAMPLES.md
- [x] Version agreement verified across pyproject.toml, __init__.py, CHANGELOG.md, release-please manifest
- [x] Clean wheel build and install smoke test (mcp-geo 0.4.0)
- [x] CLI smoke: --version, tools, providers, --dry-run all verified in clean venv
- [ ] Reconcile documentation and changelog with the final 0.4.0 tool contracts
- [ ] Publish 0.4.0 to PyPI with provenance (PyPI remains on 0.3.0)
- [ ] Add a deployed tool gallery and clean-install MCP client smoke test

## v0.5
- MBTiles and PMTiles metadata inspection
- GeoParquet read/write helpers
- Safer Overpass query budgeting for very large areas
- Example notebooks for disaster response, healthcare access, and urban planning
- Typed tool schemas with richer examples for MCP clients
- Optional PostGIS import/export helpers
- Better CRS detection and warnings for local files
- Map artifact gallery for documentation

## v1.0
- Stable public tool contracts
- Comprehensive test coverage (90%+)
- Security and performance audit for public-service defaults
