"""Tests for elevation tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from geo_mcp.elevation import elevation, elevation_profile


class TestElevation:
    @pytest.mark.asyncio
    async def test_elevation_success(self):
        """Test successful elevation query."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "elevation": 10.5,
                }
            ]
        }
        mock_response.raise_for_status = lambda: None

        with patch("geo_mcp.elevation.get_client") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await elevation(40.7128, -74.0060)

            assert result["lat"] == 40.7128
            assert result["lon"] == -74.0060
            assert result["elevation_m"] == 10.5

    @pytest.mark.asyncio
    async def test_elevation_invalid_coords(self):
        """Test elevation with invalid coordinates."""
        result = await elevation(91.0, 0.0)  # Invalid latitude
        assert "error" in result

    @pytest.mark.asyncio
    async def test_elevation_http_error(self):
        """Test elevation with HTTP error."""
        with patch("geo_mcp.elevation.get_client") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("Network error")
            )

            result = await elevation(40.0, -74.0)
            assert "error" in result


class TestElevationProfile:
    @pytest.mark.asyncio
    async def test_elevation_profile_success(self):
        """Test successful elevation profile query."""
        coords = [
            [-74.0060, 40.7128],
            [-74.0050, 40.7138],
            [-74.0040, 40.7148],
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"latitude": 40.7128, "longitude": -74.0060, "elevation": 10.5},
                {"latitude": 40.7138, "longitude": -74.0050, "elevation": 11.2},
                {"latitude": 40.7148, "longitude": -74.0040, "elevation": 12.0},
            ]
        }
        mock_response.raise_for_status = lambda: None

        with patch("geo_mcp.elevation.get_client") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await elevation_profile(coords)

            assert len(result) == 3
            assert result[0]["elevation_m"] == 10.5
            assert result[1]["elevation_m"] == 11.2
            assert result[2]["elevation_m"] == 12.0

    @pytest.mark.asyncio
    async def test_elevation_profile_too_few_points(self):
        """Test elevation profile with too few points."""
        coords = [[40.7128, -74.0060]]  # Only 1 point

        result = await elevation_profile(coords)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_elevation_profile_invalid_coords(self):
        """Test elevation profile with invalid coordinates."""
        coords = [
            [0.0, 91.0],
            [-74.0, 40.0],
        ]

        result = await elevation_profile(coords)
        assert "error" in result
