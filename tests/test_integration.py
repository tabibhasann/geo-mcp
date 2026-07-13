"""MCP server integration smoke tests."""

import json

import pytest

from geo_mcp.server import mcp


async def call_tool(name: str, arguments: dict) -> dict | list | str | float | bool:
    result = await mcp.call_tool(name, arguments)
    assert result, f"{name} returned no content"

    content = getattr(result, "content", result)
    while isinstance(content, (list, tuple)):
        assert content, f"{name} returned empty content"
        content = content[0]

    text = getattr(content, "text", content)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


@pytest.mark.asyncio
async def test_local_geometry_workspace_flow():
    point = json.dumps({"type": "Point", "coordinates": [90.4125, 23.8103]})

    buffer_result = await call_tool("buffer", {"geojson": point, "distance_m": 1000})
    assert buffer_result["type"] == "Polygon"

    store_result = await call_tool("workspace_store", {"name": "dhaka_1km", "data": json.dumps(buffer_result)})
    assert store_result["success"] is True

    retrieved = await call_tool("workspace_get", {"name": "dhaka_1km"})
    assert retrieved["name"] == "dhaka_1km"

    listed = await call_tool("workspace_list", {})
    names = {item["name"] for item in listed["results"]}
    assert "dhaka_1km" in names

    cleared = await call_tool("workspace_clear", {"name": "dhaka_1km"})
    assert cleared["success"] is True


@pytest.mark.asyncio
async def test_spatial_join_flow():
    points = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0.5, 0.5]},
                "properties": {"id": "P1"},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [5, 5]},
                "properties": {"id": "P2"},
            },
        ],
    }
    polygons = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "zone-a",
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                "properties": {},
            }
        ],
    }

    joined = await call_tool(
        "spatial_join",
        {"points_geojson": json.dumps(points), "polygons_geojson": json.dumps(polygons)},
    )

    assert joined["features"][0]["properties"]["polygon_id"] == "zone-a"
    assert joined["features"][1]["properties"]["polygon_id"] is None


@pytest.mark.asyncio
async def test_meta_tools_expose_catalog():
    catalog = await call_tool("list_all_tools", {})
    # Catalog categories are {category_name: {tool_name: {description, ...}}}
    counted = sum(len(tools) for tools in catalog["categories"].values())
    # The total matches the count of categorised tools (meta-tools are excluded)
    assert catalog["total_tools"] == counted
    assert counted >= 30
    assert "geometry" in catalog["categories"]
    assert "workspace" in catalog["categories"]
    assert "spatial_join" in catalog["categories"]["advanced"]

    suggestions = await call_tool("suggest_tools", {"task_description": "Find hospitals within 5km of Dhaka"})
    names = {item["tool_name"] for item in suggestions["suggested_tools"]}
    assert {"geocode", "osm_features", "buffer"}.issubset(names)


@pytest.mark.asyncio
async def test_tool_errors_are_mcp_safe():
    result = await call_tool("buffer", {"geojson": "not valid json", "distance_m": 100})
    assert "error" in result
    assert "hint" in result


@pytest.mark.asyncio
async def test_dry_run_geocode():
    """Dry-run mode returns mock data without hitting APIs."""
    from geo_mcp.config import settings

    original = settings.dry_run
    settings.dry_run = True
    try:
        result = await call_tool("geocode", {"query": "Dhaka", "limit": 1})
        if isinstance(result, dict) and "lat" in result:
            result = [result]
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "lat" in result[0]
        assert "lon" in result[0]
    finally:
        settings.dry_run = original


@pytest.mark.asyncio
async def test_dry_run_route():
    """Dry-run mode returns mock route data."""
    from geo_mcp.config import settings

    original = settings.dry_run
    settings.dry_run = True
    try:
        result = await call_tool(
            "route",
            {"coordinates": "[[90.41, 23.81], [90.42, 23.82]]", "profile": "driving"},
        )
        assert "distance_m" in result
        assert "duration_s" in result
        assert "geometry" in result
    finally:
        settings.dry_run = original


@pytest.mark.asyncio
async def test_dry_run_elevation():
    """Dry-run mode returns mock elevation data."""
    from geo_mcp.config import settings

    original = settings.dry_run
    settings.dry_run = True
    try:
        result = await call_tool("elevation", {"lat": 23.81, "lon": 90.41})
        assert "elevation_m" in result
    finally:
        settings.dry_run = original


def test_provider_registry():
    """Provider registry has all expected default providers."""
    from geo_mcp.providers import PROVIDER_REGISTRY

    assert "geocoding" in PROVIDER_REGISTRY
    assert "nominatim" in PROVIDER_REGISTRY["geocoding"]
    assert "routing" in PROVIDER_REGISTRY
    assert "osrm" in PROVIDER_REGISTRY["routing"]
    assert "elevation" in PROVIDER_REGISTRY
    assert "open_elevation" in PROVIDER_REGISTRY["elevation"]


def test_quota_tracker():
    """Quota tracker records calls and warns at thresholds."""
    from geo_mcp.providers import QuotaTracker

    tracker = QuotaTracker("test", daily_limit=10)
    for _ in range(8):
        tracker.record()
    assert tracker.call_count == 8
    assert tracker._warned_80 is True
    assert tracker._warned_100 is False


def test_quota_tracker_limit():
    """Quota tracker raises at 100% usage."""
    from geo_mcp.providers import QuotaTracker

    tracker = QuotaTracker("test", daily_limit=3)
    tracker.record()
    tracker.record()
    with pytest.raises(RuntimeError, match="daily limit reached"):
        tracker.record()


def test_list_providers():
    """list_providers returns all registered providers."""
    from geo_mcp.providers import list_providers

    registry = list_providers()
    assert "geocoding" in registry
    assert "nominatim" in registry["geocoding"]
    assert "routing" in registry
    assert "osrm" in registry["routing"]
