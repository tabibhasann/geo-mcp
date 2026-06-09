# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
