"""Tests for Overpass QL query builder."""

import json

import pytest

from geo_mcp.osm import build_overpass_query


class TestOverpassBuilder:
    def test_bbox_simple_query(self):
        ql = build_overpass_query([23.0, 90.0, 24.0, 91.0], {"amenity": "hospital"})
        if isinstance(ql, dict) and "error" in ql:
            pytest.fail(f"Build error: {ql}")
        assert '["amenity"="hospital"]' in ql
        assert "(23.0,90.0,24.0,91.0)" in ql
        assert "[out:json]" in ql
        assert "node" in ql.lower()
        assert "way" in ql.lower()

    def test_bbox_with_specific_types(self):
        ql = build_overpass_query(
            [23.0, 90.0, 24.0, 91.0],
            {"amenity": "hospital"},
            element_types=["node", "way"],
        )
        if isinstance(ql, dict) and "error" in ql:
            pytest.fail(f"Build error: {ql}")
        assert "node" in ql
        assert "way" in ql
        assert "relation" not in ql

    def test_tag_without_value(self):
        ql = build_overpass_query([0, 0, 1, 1], {"name": ""})
        if isinstance(ql, dict) and "error" in ql:
            pytest.fail(f"Build error: {ql}")
        assert '["name"]' in ql

    def test_multiple_tags(self):
        ql = build_overpass_query([0, 0, 1, 1], {"amenity": "school", "name": ""})
        if isinstance(ql, dict) and "error" in ql:
            pytest.fail(f"Build error: {ql}")
        assert '["amenity"="school"]' in ql
        assert '["name"]' in ql

    def test_invalid_bbox_length(self):
        result = build_overpass_query([0, 0, 0], {"amenity": "foo"})
        assert "error" in result

    def test_invalid_tags_type(self):
        result = build_overpass_query([0, 0, 1, 1], "not a dict")
        assert "error" in result

    def test_place_name_query(self):
        ql = build_overpass_query("Dhaka, Bangladesh", {"amenity": "hospital"})
        if isinstance(ql, dict) and "error" in ql:
            pytest.fail(f"Build error: {ql}")
        assert "area" in ql
        assert "Dhaka, Bangladesh" in ql

    def test_geojson_polygon_query(self):
        geojson = json.dumps({
            "type": "Polygon",
            "coordinates": [[
                [90.0, 23.0],
                [91.0, 23.0],
                [91.0, 24.0],
                [90.0, 24.0],
                [90.0, 23.0],
            ]],
        })
        ql = build_overpass_query(geojson, {"amenity": "hospital"})
        if isinstance(ql, dict) and "error" in ql:
            pytest.fail(f"Build error: {ql}")
        assert "poly:" in ql
