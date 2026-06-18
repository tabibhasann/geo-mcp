# Changelog

All notable changes to this project are documented here.
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html/).

## [0.4.0] - 2026-06-18

### Added
- AI-assisted PR review workflow (`.github/workflows/codex-review.yml`)
- GitHub issue templates (bug, feature request, good first issue) and a PR template
- `EXAMPLES.md` linking to end-to-end workflow recipes
- ASCII architecture diagram in the README
- Coverage gate (`--cov-fail-under=70`) in CI; coverage uploaded to Codecov
- System-deps install (GDAL/GEOS/PROJ) in CI for the optional `[files]` and `[raster]` extras

### Fixed
- Removed magic-number `total_tools == 42` assertion in `test_integration.py`; catalog count is computed dynamically
- `nearest_neighbor` no longer scans O(n²); uses STRtree for candidate lookup
- Workspace store no longer grows unbounded; LRU cap respected across all entry points
- Static map output is paginated; large feature collections no longer OOM the server
- `overpass_query` now reuses the shared `get_client()` (retries + rate limiting applied)

## [0.3.0] - 2026-06-09

### Added
- Isochrone tool backed by OpenRouteService
- Elevation lookup and elevation profile tools
- Advanced workflow tools: spatial query, spatial join, nearest neighbor, batch geocoding, geometry repair, and geometry validation
- Static map rendering and workspace storage tools
- Dockerfile, Compose file, and CodeQL workflow

### Fixed
- HTTP/SSE transport flag handling for current FastMCP versions
- Publish workflow now tolerates reruns for already-uploaded PyPI files
- `nearest_road` coordinate validation import
- README duplication and release documentation

## [0.2.1] - 2026-06-01

### Fixed
- Consistent mcp-geo branding across all documentation
- CI workflow using uv with proper dependency groups

## [0.1.0] - 2026-06-01

### Added
- Initial release with 20+ geospatial MCP tools
- Geometry operations: buffer, distance, area, length, centroid, simplify, convex_hull, bbox, spatial_predicate, transform_crs, validate_geojson
- Geocoding: forward and reverse via Nominatim
- OSM/Overpass: query builder + executor returning GeoJSON
- Routing: route, matrix, nearest road via OSRM
- Optional vector file support (geopandas/pyogrio)
- Optional raster support (rasterio/rasterstats)
- Configurable provider URLs and rate limiting
- Tool-safe error handling
