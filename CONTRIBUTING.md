# Contributing to geo-mcp

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
- Wrap with `safe_tool` or `async_safe_tool` from `geo_mcp.errors`
- Network tools use `geo_mcp.http.get_client()` for shared User-Agent/timeout
- GeoJSON is always EPSG:4326 with `[lon, lat]` coordinate order
- Area/length on WGS84 must be geodesic via `pyproj.Geod`
- Providers live in `src/geo_mcp/providers/` — subclass the ABC and register in `PROVIDER_REGISTRY`

## Testing

- Every new tool or provider needs tests in `tests/`
- Mock external HTTP calls — never hit real APIs in tests
- Aim for >70% coverage (enforced in CI)
- Run: `pytest tests/ -v --cov=geo_mcp`

## CI

GitHub Actions runs ruff, mypy, and pytest on every PR. All must pass before merge.

## Pull request process

1. Keep PRs focused — one feature or fix per PR
2. Update the CHANGELOG if applicable
3. Ensure all CI checks pass
4. Request review from a maintainer

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
