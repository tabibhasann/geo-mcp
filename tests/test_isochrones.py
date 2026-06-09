"""Tests for isochrone tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from geo_mcp.isochrones import isochrone


class TestIsochrone:
    @pytest.mark.asyncio
    async def test_isochrone_success(self):
        """Test successful isochrone query."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                    "properties": {
                        "value": 300,
                        "center": [0.5, 0.5],
                    },
                }
            ],
        }
        mock_response.raise_for_status = lambda: None

        # Mock settings to provide API key
        with patch("geo_mcp.isochrones.settings") as mock_settings:
            mock_settings.ors_api_key = "test_api_key"
            mock_settings.ors_url = "https://api.openrouteservice.org"

            with patch("geo_mcp.isochrones.get_client") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

                result = await isochrone(40.7128, -74.0060, profile="driving-car", range_type="time", range_value=300)

                assert result["type"] == "FeatureCollection"
                assert len(result["features"]) == 1
                assert result["features"][0]["geometry"]["type"] == "Polygon"
                payload = mock_client.return_value.__aenter__.return_value.post.call_args.kwargs["json"]
                assert payload["range"] == [300]

    @pytest.mark.asyncio
    async def test_isochrone_invalid_coords(self):
        """Test isochrone with invalid coordinates."""
        result = await isochrone(91.0, 0.0)  # Invalid latitude
        assert "error" in result

    @pytest.mark.asyncio
    async def test_isochrone_invalid_profile(self):
        """Test isochrone with invalid profile."""
        result = await isochrone(40.0, -74.0, profile="invalid-profile")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_isochrone_invalid_range_type(self):
        """Test isochrone with invalid range type."""
        result = await isochrone(40.0, -74.0, range_type="invalid")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_isochrone_negative_range(self):
        """Test isochrone with negative range value."""
        result = await isochrone(40.0, -74.0, range_value=-100)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_isochrone_http_error(self):
        """Test isochrone with HTTP error."""
        with patch("geo_mcp.isochrones.settings") as mock_settings:
            mock_settings.ors_api_key = "test_api_key"
            mock_settings.ors_url = "https://api.openrouteservice.org"

            with patch("geo_mcp.isochrones.get_client") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=httpx.HTTPError("Network error")
                )

                result = await isochrone(40.0, -74.0)
                assert "error" in result

    @pytest.mark.asyncio
    async def test_isochrone_distance_range(self):
        """Test isochrone with distance range type."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [],
        }
        mock_response.raise_for_status = lambda: None

        with patch("geo_mcp.isochrones.settings") as mock_settings:
            mock_settings.ors_api_key = "test_api_key"
            mock_settings.ors_url = "https://api.openrouteservice.org"

            with patch("geo_mcp.isochrones.get_client") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

                result = await isochrone(40.0, -74.0, range_type="distance", range_value=1000)

                assert result["type"] == "FeatureCollection"
                payload = mock_client.return_value.__aenter__.return_value.post.call_args.kwargs["json"]
                assert payload["range"] == [1000]
