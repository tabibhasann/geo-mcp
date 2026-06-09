"""Tests for advanced spatial tools."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from geo_mcp.advanced import (
    _geocode_cache,
    batch_geocode,
    build_spatial_index,
    cached_geocode,
    nearest_neighbor,
    repair_geometry,
    spatial_join,
    spatial_query,
    validate_geometry,
)


@pytest.fixture(autouse=True)
def clear_geocode_cache():
    _geocode_cache.clear()
    yield
    _geocode_cache.clear()


@pytest.fixture
def sample_feature_collection():
    """Create a sample FeatureCollection for testing."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {"id": 1, "name": "Point 1"},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1, 1]},
                "properties": {"id": 2, "name": "Point 2"},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [2, 2]},
                "properties": {"id": 3, "name": "Point 3"},
            },
        ],
    }


class TestBuildSpatialIndex:
    def test_build_spatial_index_success(self, sample_feature_collection):
        """Test building spatial index."""
        result = build_spatial_index(json.dumps(sample_feature_collection))

        assert result["feature_count"] == 3
        assert result["index_type"] == "STRtree"
        assert "bounds" in result

    def test_build_spatial_index_empty_collection(self):
        """Test building spatial index with empty collection."""
        empty_fc = {"type": "FeatureCollection", "features": []}
        result = build_spatial_index(json.dumps(empty_fc))

        assert result["feature_count"] == 0

    def test_build_spatial_index_invalid_json(self):
        """Test building spatial index with invalid JSON."""
        result = build_spatial_index("not valid json")
        assert "error" in result


class TestSpatialQuery:
    def test_spatial_query_intersects(self, sample_feature_collection):
        """Test spatial query with intersects predicate."""
        query_geom = json.dumps(
            {"type": "Polygon", "coordinates": [[[-1, -1], [1.5, -1], [1.5, 1.5], [-1, 1.5], [-1, -1]]]}
        )

        result = spatial_query(json.dumps(sample_feature_collection), query_geom, "intersects")

        result_fc = json.loads(result)
        assert result_fc["type"] == "FeatureCollection"
        assert len(result_fc["features"]) == 2  # Points at (0,0) and (1,1)

    def test_spatial_query_within(self, sample_feature_collection):
        """Test spatial query with within predicate."""
        query_geom = json.dumps(
            {"type": "Polygon", "coordinates": [[[-1, -1], [2.5, -1], [2.5, 2.5], [-1, 2.5], [-1, -1]]]}
        )

        result = spatial_query(json.dumps(sample_feature_collection), query_geom, "within")

        result_fc = json.loads(result)
        assert len(result_fc["features"]) == 3

    def test_spatial_query_no_matches(self, sample_feature_collection):
        """Test spatial query with no matching features."""
        query_geom = json.dumps(
            {"type": "Polygon", "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]]}
        )

        result = spatial_query(json.dumps(sample_feature_collection), query_geom, "intersects")

        result_fc = json.loads(result)
        assert len(result_fc["features"]) == 0


class TestSpatialJoin:
    def test_spatial_join_success(self):
        """Test spatial join between points and polygons."""
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
                    "geometry": {"type": "Point", "coordinates": [1.5, 1.5]},
                    "properties": {"id": "P2"},
                },
            ],
        }

        polygons = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                    "properties": {"polygon_id": "A"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]]},
                    "properties": {"polygon_id": "B"},
                },
            ],
        }

        result = spatial_join(json.dumps(points), json.dumps(polygons))
        result_fc = json.loads(result)

        assert len(result_fc["features"]) == 2
        # Check that polygon_id was added to properties
        for feature in result_fc["features"]:
            assert "polygon_id" in feature["properties"]

    def test_spatial_join_no_match(self):
        """Test spatial join where points don't match any polygon."""
        points = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10, 10]}, "properties": {"id": "P1"}}
            ],
        }

        polygons = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                    "properties": {"polygon_id": "A"},
                }
            ],
        }

        result = spatial_join(json.dumps(points), json.dumps(polygons))
        result_fc = json.loads(result)

        assert len(result_fc["features"]) == 1
        assert result_fc["features"][0]["properties"]["polygon_id"] is None


class TestCachedGeocode:
    @pytest.mark.asyncio
    async def test_cached_geocode_first_call(self):
        """Test cached geocode on first call (cache miss)."""
        # Mock the geocode function
        with patch("geo_mcp.advanced.geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = [{"lat": 40.7128, "lon": -74.0060, "display_name": "New York"}]

            result = await cached_geocode("New York, USA", limit=1)

            assert result["cached"] is False
            assert len(result["matches"]) > 0
            mock_geocode.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_geocode_second_call(self):
        """Test cached geocode on second call (cache hit)."""
        # Mock the geocode function
        with patch("geo_mcp.advanced.geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = [{"lat": 42.3601, "lon": -71.0589, "display_name": "Boston"}]

            # First call
            await cached_geocode("Boston, USA", limit=1)

            # Second call should use cache (geocode should not be called again)
            result = await cached_geocode("Boston, USA", limit=1)

            assert result["cached"] is True
            assert len(result["matches"]) > 0
            # geocode should only be called once due to caching
            assert mock_geocode.call_count == 1


class TestBatchGeocode:
    @pytest.mark.asyncio
    async def test_batch_geocode_success(self):
        """Test batch geocoding."""
        addresses = ["Paris, France", "London, UK"]

        with patch("geo_mcp.advanced.geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = [{"lat": 0, "lon": 0, "display_name": "Mock"}]
            result = await batch_geocode(addresses, limit=1)

        assert result["total"] == 2
        assert "cache_hits" in result
        assert "cache_misses" in result
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_batch_geocode_with_caching(self):
        """Test batch geocoding with repeated addresses."""
        addresses = ["Unique Repeated Test Address", "Unique Repeated Test Address"]

        with patch("geo_mcp.advanced.geocode", new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = [{"lat": 0, "lon": 0, "display_name": "Mock"}]
            result = await batch_geocode(addresses, limit=1)

        assert result["total"] == 2
        # Second occurrence should be a cache hit
        assert result["cache_hits"] >= 1


class TestNearestNeighbor:
    def test_nearest_neighbor_success(self, sample_feature_collection):
        """Test nearest neighbor search."""
        query_point = json.dumps({"type": "Point", "coordinates": [0.5, 0.5]})

        result = nearest_neighbor(query_point, json.dumps(sample_feature_collection), k=2)

        result_fc = json.loads(result)
        assert result_fc["type"] == "FeatureCollection"
        assert len(result_fc["features"]) == 2

        # Check that distance was added
        for feature in result_fc["features"]:
            assert "distance_to_query" in feature["properties"]

    def test_nearest_neighbor_k_larger_than_collection(self, sample_feature_collection):
        """Test nearest neighbor with k larger than collection size."""
        query_point = json.dumps({"type": "Point", "coordinates": [0, 0]})

        result = nearest_neighbor(query_point, json.dumps(sample_feature_collection), k=10)

        result_fc = json.loads(result)
        assert len(result_fc["features"]) == 3  # Only 3 features available


class TestRepairGeometry:
    def test_repair_valid_geometry(self):
        """Test repairing already valid geometry."""
        valid_polygon = json.dumps({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]})

        result = repair_geometry(valid_polygon)

        # Should return the same geometry
        result_geom = json.loads(result)
        assert result_geom["type"] == "Polygon"

    def test_repair_invalid_bowtie(self):
        """Test repairing invalid bowtie polygon."""
        # Bowtie polygon (self-intersecting)
        invalid_polygon = json.dumps({"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]})

        result = repair_geometry(invalid_polygon)

        # Should be repaired
        result_geom = json.loads(result)
        assert result_geom["type"] in ["Polygon", "MultiPolygon"]

    def test_repair_invalid_json(self):
        """Test repairing with invalid JSON."""
        result = repair_geometry("not valid json")
        assert "error" in result


class TestValidateGeometry:
    def test_validate_valid_polygon(self):
        """Test validating valid polygon."""
        valid_polygon = json.dumps({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]})

        result = validate_geometry(valid_polygon)

        assert result["is_valid"] is True
        assert result["parseable"] is True
        assert result["geometry_type"] == "Polygon"
        assert len(result["issues"]) == 0

    def test_validate_invalid_polygon(self):
        """Test validating invalid polygon."""
        # Bowtie polygon
        invalid_polygon = json.dumps({"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]})

        result = validate_geometry(invalid_polygon)

        assert result["is_valid"] is False
        assert result["parseable"] is True
        assert result["can_repair"] is True
        assert len(result["issues"]) > 0

    def test_validate_point(self):
        """Test validating point geometry."""
        point = json.dumps({"type": "Point", "coordinates": [0, 0]})

        result = validate_geometry(point)

        assert result["is_valid"] is True
        assert result["geometry_type"] == "Point"

    def test_validate_invalid_json(self):
        """Test validating invalid JSON."""
        result = validate_geometry("not valid json")

        assert result["is_valid"] is False
        assert result["parseable"] is False
        assert "error" in result

    def test_validate_empty_geometry(self):
        """Test validating empty geometry."""
        empty_polygon = json.dumps({"type": "Polygon", "coordinates": []})

        result = validate_geometry(empty_polygon)

        # Empty geometries are typically invalid
        assert result["parseable"] is True
