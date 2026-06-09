"""Tests for vector file tools."""

import json
import tempfile
from pathlib import Path

import pytest

from geo_mcp.vector import vector_info, vector_read

pytest.importorskip("geopandas")
pytest.importorskip("pyogrio")


class TestVectorInfo:
    def test_vector_info_geojson(self):
        """Test vector_info with GeoJSON file."""
        # Create a temporary GeoJSON file
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"name": "Point 1", "value": 100},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [1, 1]},
                    "properties": {"name": "Point 2", "value": 200},
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
            json.dump(geojson_data, f)
            temp_path = f.name

        try:
            result = vector_info(temp_path)

            assert result["driver"] == "GeoJSON"
            assert result["feature_count"] == 2
            assert "Point" in result["geometry_types"]
            assert "name" in result["fields"]
            assert "value" in result["fields"]
            assert result["crs"] == "EPSG:4326"
        finally:
            Path(temp_path).unlink()

    def test_vector_info_nonexistent_file(self):
        """Test vector_info with nonexistent file."""
        result = vector_info("/nonexistent/file.geojson")
        assert "error" in result

    def test_vector_info_invalid_file(self):
        """Test vector_info with invalid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
            f.write("not valid json")
            temp_path = f.name

        try:
            result = vector_info(temp_path)
            assert "error" in result
        finally:
            Path(temp_path).unlink()


class TestVectorRead:
    def test_vector_read_geojson(self):
        """Test vector_read with GeoJSON file."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"name": "Point 1", "value": 100},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [1, 1]},
                    "properties": {"name": "Point 2", "value": 200},
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
            json.dump(geojson_data, f)
            temp_path = f.name

        try:
            result = vector_read(temp_path)

            assert result["type"] == "FeatureCollection"
            assert len(result["features"]) == 2
            assert result["features"][0]["properties"]["name"] == "Point 1"
            assert result["features"][1]["properties"]["value"] == 200
        finally:
            Path(temp_path).unlink()

    def test_vector_read_with_bbox_filter(self):
        """Test vector_read with bbox filter."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"name": "Inside"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 10]},
                    "properties": {"name": "Outside"},
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
            json.dump(geojson_data, f)
            temp_path = f.name

        try:
            # Bbox that only includes the first point
            result = vector_read(temp_path, bbox=[-1, -1, 1, 1])

            assert len(result["features"]) == 1
            assert result["features"][0]["properties"]["name"] == "Inside"
        finally:
            Path(temp_path).unlink()

    def test_vector_read_with_where_filter(self):
        """Test vector_read with where filter."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0, 0]}, "properties": {"value": 100}},
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [1, 1]}, "properties": {"value": 200}},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
            json.dump(geojson_data, f)
            temp_path = f.name

        try:
            result = vector_read(temp_path, where="value > 150")

            assert len(result["features"]) == 1
            assert result["features"][0]["properties"]["value"] == 200
        finally:
            Path(temp_path).unlink()

    def test_vector_read_with_limit(self):
        """Test vector_read with result limit."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [i, i]}, "properties": {"id": i}}
                for i in range(10)
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
            json.dump(geojson_data, f)
            temp_path = f.name

        try:
            result = vector_read(temp_path, limit=5)

            assert len(result["features"]) == 5
            assert result["metadata"]["total_features"] == 10
        finally:
            Path(temp_path).unlink()

    def test_vector_read_nonexistent_file(self):
        """Test vector_read with nonexistent file."""
        result = vector_read("/nonexistent/file.geojson")
        assert "error" in result
