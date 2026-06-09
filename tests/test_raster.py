"""Tests for raster file tools."""

import tempfile
from pathlib import Path

import pytest

from geo_mcp.raster import raster_info, sample_raster, zonal_stats

np = pytest.importorskip("numpy")
pytest.importorskip("rasterio")
pytest.importorskip("rasterstats")


@pytest.fixture
def sample_raster_file():
    """Create a temporary raster file for testing."""
    import rasterio
    from rasterio.transform import from_bounds

    # Create a simple 10x10 raster
    data = np.random.rand(10, 10).astype(np.float32)

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
        temp_path = f.name

    try:
        with rasterio.open(
            temp_path,
            "w",
            driver="GTiff",
            height=10,
            width=10,
            count=1,
            dtype=np.float32,
            crs="EPSG:4326",
            transform=from_bounds(0, 0, 1, 1, 10, 10),
        ) as dst:
            dst.write(data, 1)

        yield temp_path
    finally:
        Path(temp_path).unlink()


class TestRasterInfo:
    def test_raster_info_success(self, sample_raster_file):
        """Test raster_info with valid raster file."""
        result = raster_info(sample_raster_file)

        assert result["crs"] == "EPSG:4326"
        assert result["bands"] == 1
        assert result["width"] == 10
        assert result["height"] == 10
        assert len(result["bounds"]) == 4
        assert len(result["res"]) == 2

    def test_raster_info_nonexistent_file(self):
        """Test raster_info with nonexistent file."""
        result = raster_info("/nonexistent/file.tif")
        assert "error" in result


class TestZonalStats:
    def test_zonal_stats_success(self, sample_raster_file):
        """Test zonal_stats with valid inputs."""
        zones_geojson = {
            "type": "Polygon",
            "coordinates": [[[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8], [0.2, 0.2]]],
        }

        result = zonal_stats(sample_raster_file, zones_geojson)

        assert isinstance(result, list)
        assert len(result) > 0
        assert "min" in result[0]
        assert "max" in result[0]
        assert "mean" in result[0]
        assert "count" in result[0]

    def test_zonal_stats_with_geojson_string(self, sample_raster_file):
        """Test zonal_stats with GeoJSON string."""
        import json

        zones_geojson = json.dumps(
            {"type": "Polygon", "coordinates": [[[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8], [0.2, 0.2]]]}
        )

        result = zonal_stats(sample_raster_file, zones_geojson)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_zonal_stats_nonexistent_raster(self):
        """Test zonal_stats with nonexistent raster."""
        zones = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
        result = zonal_stats("/nonexistent/file.tif", zones)
        assert "error" in result


class TestSampleRaster:
    def test_sample_raster_point(self, sample_raster_file):
        """Test sample_raster with single point."""
        point_geojson = {"type": "Point", "coordinates": [0.5, 0.5]}

        result = sample_raster(sample_raster_file, point_geojson)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "lon" in result[0]
        assert "lat" in result[0]
        assert "values" in result[0]

    def test_sample_raster_multipoint(self, sample_raster_file):
        """Test sample_raster with multiple points."""
        points_geojson = {"type": "MultiPoint", "coordinates": [[0.3, 0.3], [0.7, 0.7]]}

        result = sample_raster(sample_raster_file, points_geojson)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_sample_raster_feature_collection(self, sample_raster_file):
        """Test sample_raster with FeatureCollection."""
        fc_geojson = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0.5, 0.5]}, "properties": {}}
            ],
        }

        result = sample_raster(sample_raster_file, fc_geojson)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_sample_raster_with_string(self, sample_raster_file):
        """Test sample_raster with GeoJSON string."""
        import json

        point_geojson = json.dumps({"type": "Point", "coordinates": [0.5, 0.5]})

        result = sample_raster(sample_raster_file, point_geojson)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_sample_raster_out_of_bounds(self, sample_raster_file):
        """Test sample_raster with point outside raster bounds."""
        point_geojson = {
            "type": "Point",
            "coordinates": [10.0, 10.0],  # Outside 0-1 bounds
        }

        result = sample_raster(sample_raster_file, point_geojson)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["values"] is None

    def test_sample_raster_nonexistent_file(self):
        """Test sample_raster with nonexistent file."""
        point = {"type": "Point", "coordinates": [0.5, 0.5]}
        result = sample_raster("/nonexistent/file.tif", point)
        assert "error" in result
