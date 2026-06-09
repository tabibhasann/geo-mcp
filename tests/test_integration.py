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
    assert catalog["total_tools"] == 42
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
