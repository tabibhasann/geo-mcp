"""Comprehensive error path tests for geo-mcp tool functions.

Tests invalid inputs, edge cases, and error handling across all tool categories.
"""

import json

import pytest

from geo_mcp import geometry, osm, routing, validation, workspace
from geo_mcp.units import convert_area, convert_length, parse_geojson


class TestGeometryErrors:
    """Error tests for geometry tools."""

    def test_buffer_negative_distance(self, point_geojson: str) -> None:
        result = geometry.buffer(point_geojson, -100)
        assert "error" in result

    def test_buffer_invalid_geojson(self) -> None:
        result = geometry.buffer("not valid geojson", 100)
        assert "error" in result

    def test_buffer_empty_geojson(self) -> None:
        result = geometry.buffer(json.dumps({"type": "Point", "coordinates": []}), 100)
        assert "error" in result

    def test_distance_invalid_geojson_a(self, point_geojson: str) -> None:
        result = geometry.distance("invalid", point_geojson)
        assert "error" in result

    def test_distance_invalid_geojson_b(self, point_geojson: str) -> None:
        result = geometry.distance(point_geojson, "invalid")
        assert "error" in result

    def test_area_invalid_geojson(self) -> None:
        result = geometry.area("not geojson")
        assert "error" in result

    def test_area_unknown_unit(self, polygon_geojson: str) -> None:
        result = geometry.area(polygon_geojson, "lightyears")
        assert "error" in result

    def test_length_unknown_unit(self, linestring_geojson: str) -> None:
        result = geometry.length(linestring_geojson, "parsecs")
        assert "error" in result

    def test_spatial_predicate_unknown_op(self, point_geojson: str, polygon_geojson: str) -> None:
        result = geometry.spatial_predicate(point_geojson, polygon_geojson, "beyond")
        assert "error" in result

    def test_spatial_predicate_invalid_geojson(self) -> None:
        result = geometry.spatial_predicate("bad", "also bad", "intersects")
        assert "error" in result

    def test_transform_crs_invalid_crs(self, point_geojson: str) -> None:
        result = geometry.transform_crs(point_geojson, "INVALID:9999", "EPSG:4326")
        assert "error" in result

    def test_validate_geojson_invalid_json(self) -> None:
        result = geometry.validate_geojson("not json at all")
        assert result["valid"] is False
        assert "errors" in result

    def test_validate_geojson_empty_string(self) -> None:
        result = geometry.validate_geojson("")
        assert result["valid"] is False
        assert "errors" in result

    def test_centroid_invalid_geojson(self) -> None:
        result = geometry.centroid("not geojson")
        assert "error" in result

    def test_simplify_invalid_tolerance(self, point_geojson: str) -> None:
        result = geometry.simplify(point_geojson, -1.0)
        assert "error" in result or "type" in result

    def test_convex_hull_invalid_geojson(self) -> None:
        result = geometry.convex_hull("bad input")
        assert "error" in result

    def test_bbox_invalid_geojson(self) -> None:
        result = geometry.bbox("not geojson")
        assert "error" in result


class TestOSMErrors:
    """Error tests for OSM tools."""

    def test_build_overpass_query_invalid_area_type(self) -> None:
        result = osm.build_overpass_query(12345, {"amenity": "hospital"})
        assert "error" in result

    def test_build_overpass_query_bbox_wrong_length(self) -> None:
        result = osm.build_overpass_query([1, 2, 3], {"amenity": "hospital"})
        assert "error" in result

    def test_build_overpass_query_invalid_tags_type(self) -> None:
        result = osm.build_overpass_query([0, 0, 1, 1], "not a dict")
        assert "error" in result

    def test_build_overpass_query_invalid_element_type(self) -> None:
        result = osm.build_overpass_query(
            [0, 0, 1, 1], {"amenity": "hospital"}, element_types=["building"]
        )
        assert "error" in result

    def test_build_overpass_query_empty_tags(self) -> None:
        result = osm.build_overpass_query([0, 0, 1, 1], {})
        assert isinstance(result, str)
        assert "out" in result


class TestRoutingErrors:
    """Error tests for routing tools."""

    async def test_route_invalid_profile(self) -> None:
        result = await routing.route("[[90.4, 23.8], [90.5, 23.9]]", profile="flying")
        assert "error" in result

    async def test_route_single_coordinate(self) -> None:
        result = await routing.route("[[90.4, 23.8]]")
        assert "error" in result

    async def test_route_empty_coordinates(self) -> None:
        result = await routing.route("[]")
        assert "error" in result

    async def test_route_invalid_coordinate_format(self) -> None:
        result = await routing.route("[[90.4]]")
        assert "error" in result

    async def test_route_invalid_lat(self) -> None:
        result = await routing.route("[[90.4, 999], [90.5, 23.9]]")
        assert "error" in result

    async def test_route_invalid_lon(self) -> None:
        result = await routing.route("[[999, 23.8], [90.5, 23.9]]")
        assert "error" in result

    async def test_route_matrix_invalid_profile(self) -> None:
        result = await routing.route_matrix(
            "[[90.4, 23.8]]", "[[90.5, 23.9]]", profile="teleport"
        )
        assert "error" in result

    async def test_route_matrix_empty_sources(self) -> None:
        result = await routing.route_matrix("[]", "[[90.5, 23.9]]")
        assert "error" in result

    async def test_nearest_road_invalid_lat(self) -> None:
        result = await routing.nearest_road(999, 90.4)
        assert "error" in result

    async def test_nearest_road_invalid_profile(self) -> None:
        result = await routing.nearest_road(23.8, 90.4, profile="rocket")
        assert "error" in result


class TestValidationErrors:
    """Error tests for validation utilities."""

    def test_validate_lat_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="lat"):
            validation.validate_lat(91.0)

    def test_validate_lat_negative_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="lat"):
            validation.validate_lat(-91.0)

    def test_validate_lon_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="lon"):
            validation.validate_lon(181.0)

    def test_validate_lon_negative_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="lon"):
            validation.validate_lon(-181.0)

    def test_validate_bbox_wrong_length(self) -> None:
        with pytest.raises(ValueError, match="bbox"):
            validation.validate_bbox([1, 2, 3])

    def test_validate_bbox_south_greater_than_north(self) -> None:
        with pytest.raises(ValueError, match="south"):
            validation.validate_bbox([10, 0, 5, 10])

    def test_validate_positive_zero(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            validation.validate_positive(0, "distance")

    def test_validate_positive_negative(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            validation.validate_positive(-5, "distance")

    def test_validate_non_negative_negative(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            validation.validate_non_negative(-1, "distance")


class TestUnitsErrors:
    """Error tests for unit conversion utilities."""

    def test_convert_length_unknown_unit(self) -> None:
        with pytest.raises(ValueError, match="Unknown length unit"):
            convert_length(100, "m", "lightyears")

    def test_convert_area_unknown_unit(self) -> None:
        with pytest.raises(ValueError, match="Unknown area unit"):
            convert_area(100, "m2", "hectares2")

    def test_parse_geojson_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="Invalid GeoJSON"):
            parse_geojson("not json")

    def test_parse_geojson_empty_string(self) -> None:
        with pytest.raises(ValueError, match="Invalid GeoJSON"):
            parse_geojson("")


class TestWorkspaceErrors:
    """Error tests for workspace tools."""

    def test_workspace_get_nonexistent(self) -> None:
        workspace.workspace_clear()
        result = workspace.workspace_get("does_not_exist")
        assert "error" in result
        assert "available" in result

    def test_workspace_store_invalid_json(self) -> None:
        result = workspace.workspace_store("test", "not valid json")
        assert "error" in result
        assert "Invalid JSON" in result["error"]

    def test_workspace_clear_nonexistent(self) -> None:
        workspace.workspace_clear()
        result = workspace.workspace_clear("nonexistent")
        assert "error" in result

    def test_workspace_rename_nonexistent(self) -> None:
        workspace.workspace_clear()
        result = workspace.workspace_rename("old", "new")
        assert "error" in result

    def test_workspace_rename_to_existing(self) -> None:
        workspace.workspace_clear()
        workspace.workspace_store("item1", '{"type": "test"}')
        workspace.workspace_store("item2", '{"type": "test"}')
        result = workspace.workspace_rename("item1", "item2")
        assert "error" in result
        workspace.workspace_clear()


class TestProviderErrors:
    """Error tests for provider system."""

    def test_get_geocoding_provider_unknown(self) -> None:
        from geo_mcp.config import settings
        from geo_mcp.providers import get_geocoding_provider

        original = settings.geocoding_provider
        settings.geocoding_provider = "nonexistent"
        try:
            with pytest.raises(ValueError, match="Unknown geocoding provider"):
                get_geocoding_provider()
        finally:
            settings.geocoding_provider = original

    def test_get_routing_provider_unknown(self) -> None:
        from geo_mcp.config import settings
        from geo_mcp.providers import get_routing_provider

        original = settings.routing_provider
        settings.routing_provider = "nonexistent"
        try:
            with pytest.raises(ValueError, match="Unknown routing provider"):
                get_routing_provider()
        finally:
            settings.routing_provider = original

    def test_get_elevation_provider_unknown(self) -> None:
        from geo_mcp.config import settings
        from geo_mcp.providers import get_elevation_provider

        original = settings.elevation_provider
        settings.elevation_provider = "nonexistent"
        try:
            with pytest.raises(ValueError, match="Unknown elevation provider"):
                get_elevation_provider()
        finally:
            settings.elevation_provider = original


class TestMetaToolsErrors:
    """Error tests for meta tools."""

    def test_suggest_tools_empty_string(self) -> None:
        from geo_mcp.meta_tools import suggest_tools

        result = suggest_tools("")
        assert "suggested_tools" in result
        assert isinstance(result["suggested_tools"], list)

    def test_suggest_tools_unknown_task(self) -> None:
        from geo_mcp.meta_tools import suggest_tools

        result = suggest_tools("xyzzy flibber")
        assert "suggested_tools" in result
        assert "workflow_hint" in result

    def test_list_all_tools_structure(self) -> None:
        from geo_mcp.meta_tools import list_all_tools

        result = list_all_tools()
        assert "categories" in result
        assert "total_tools" in result
        assert result["total_tools"] > 0
