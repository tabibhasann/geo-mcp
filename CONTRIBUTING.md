# Contributing to mcp-geo

Thanks for your interest in contributing!

## Getting started

1. Fork the repo and clone locally
2. Install dev deps: `pip install -e ".[dev]"`
3. Create a branch: `git checkout -b feat/your-feature`
4. Make changes, add tests
5. Run: `ruff check src/ tests/ && mypy src/ && pytest tests/ -v`
6. Submit a PR

## Tool conventions

- New tools go in dedicated modules under `src/geo_mcp/`
- Wrap with `@safe_tool` or `@async_safe_tool` from `geo_mcp.errors`
- Network tools use `geo_mcp.http.get_client()` for shared User-Agent/timeout
- GeoJSON is always EPSG:4326 with `[lon, lat]` coordinate order
- Area/length on WGS84 must be geodesic via `pyproj.Geod`

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
