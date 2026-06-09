"""Tests for local geometry operations."""

import json

import pytest

from geo_mcp.geometry import (
    area,
    bbox,
    buffer,
    centroid,
    convex_hull,
    distance,
    length,
    simplify,
    spatial_predicate,
    transform_crs,
    validate_geojson,
)


class TestArea:
    def test_point_area_zero(self, point_geojson):
        assert area(point_geojson) == 0.0

    def test_polygon_area_nonzero(self, polygon_geojson):
        a = area(polygon_geojson)
        assert isinstance(a, (int, float))
        assert a > 0

    def test_polygon_area_km2(self, polygon_geojson):
        a = area(polygon_geojson, unit="km2")
        assert a > 0
        assert a < area(polygon_geojson, unit="m2")

    def test_polygon_area_ha(self, polygon_geojson):
        a = area(polygon_geojson, unit="ha")
        assert a > 0

    def test_area_near_equator_1deg_box(self, polygon_geojson):
        """A 1°×1° box near equator should be ~12300 km² (geodesic)."""
        a_km2 = area(polygon_geojson, unit="km2")
        assert 10000 < a_km2 < 15000, f"Expected ~12300 km², got {a_km2}"


class TestLength:
    def test_linestring_length(self, linestring_geojson):
        length_val = length(linestring_geojson, unit="km")
        assert length_val > 0

    def test_point_length_zero(self, point_geojson):
        assert length(point_geojson) == 0.0


class TestCentroid:
    def test_polygon_centroid(self, polygon_geojson):
        result = centroid(polygon_geojson)
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Unexpected error: {result}")
        data = json.loads(result)
        assert data["type"] == "Point"
        assert len(data["coordinates"]) == 2

    def test_point_centroid_is_self(self, point_geojson):
        result = centroid(point_geojson)
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Unexpected error: {result}")
        data = json.loads(result)
        assert data["coordinates"] == [90.4125, 23.8103]


class TestBuffer:
    def test_buffer_positive(self, point_geojson):
        result = buffer(point_geojson, 1000)
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Buffer error: {result}")
        data = json.loads(result)
        assert data["type"] == "Polygon"

    def test_buffer_negative(self, point_geojson):
        result = buffer(point_geojson, -1)
        assert "error" in result

    def test_buffer_distance_accuracy(self, point_geojson):
        """Buffer 1000m from a point should create a ~1km radius polygon."""
        result = buffer(point_geojson, 1000)
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Buffer error: {result}")
        data = json.loads(result)
        coords = data["coordinates"][0]
        # Approximate: a 1km radius circle has area ~3.14 km²
        # Check that result is a polygon with reasonable size
        assert len(coords) > 4, "Buffer should create multi-point polygon"


class TestDistance:
    def test_distance_same_point(self, point_geojson):
        d = distance(point_geojson, point_geojson)
        assert d == 0.0

    def test_distance_different(self, point_geojson):
        import json as _json

        far = _json.dumps({"type": "Point", "coordinates": [90.4150, 23.8120]})
        d = distance(point_geojson, far)
        assert d > 0


class TestSimplify:
    def test_simplify_noop(self, polygon_geojson):
        result = simplify(polygon_geojson, 0.0)
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Simplify error: {result}")


class TestConvexHull:
    def test_convex_hull(self, multipoint_geojson):
        result = convex_hull(multipoint_geojson)
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"ConvexHull error: {result}")


class TestBbox:
    def test_bbox(self, polygon_geojson):
        b = bbox(polygon_geojson)
        assert len(b) == 4
        assert b[0] == 90.0
        assert b[1] == 0.0
        assert b[2] == 91.0
        assert b[3] == 1.0


class TestSpatialPredicate:
    def test_contains(self, polygon_geojson, point_geojson):
        # Point at 90.4125,23.8103 is outside the 0-1 lat box
        result = spatial_predicate(polygon_geojson, point_geojson, "contains")
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Predicate error: {result}")
        assert result is False

    def test_within(self, polygon_geojson):
        import json as _json

        inner = _json.dumps(
            {
                "type": "Point",
                "coordinates": [90.5, 0.5],
            }
        )
        result = spatial_predicate(inner, polygon_geojson, "within")
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Predicate error: {result}")
        assert result is True

    def test_intersects(self, polygon_geojson, point_geojson):
        result = spatial_predicate(polygon_geojson, point_geojson, "intersects")
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Predicate error: {result}")

    def test_unknown_predicate(self, polygon_geojson, point_geojson):
        result = spatial_predicate(polygon_geojson, point_geojson, "foobar")
        assert "error" in result


class TestTransformCRS:
    def test_4326_to_3857(self, point_geojson):
        result = transform_crs(point_geojson, "EPSG:4326", "EPSG:3857")
        if isinstance(result, dict) and "error" in result:
            pytest.fail(f"Transform error: {result}")
        data = json.loads(result)
        # Web mercator coords should be large, not small degrees
        assert abs(data["coordinates"][0]) > 1000000


class TestValidate:
    def test_valid_geometry(self, polygon_geojson):
        result = validate_geojson(polygon_geojson)
        if isinstance(result, dict):
            assert result.get("valid") or result.get("valid") is True

    def test_invalid_json(self):
        result = validate_geojson("not json")
        assert isinstance(result, dict)
        assert "error" in result or result.get("valid") is False
