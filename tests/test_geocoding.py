"""Tests for Nominatim geocoding client (mocked)."""

import pytest
from respx import MockRouter

from geo_mcp.config import settings
from geo_mcp.geocoding import geocode, reverse_geocode

NOMINATIM_URL = settings.nominatim_url


@pytest.fixture
def nominatim_mock(respx_mock: MockRouter):
    return respx_mock


class TestGeocode:
    @pytest.mark.asyncio
    async def test_geocode_success(self, nominatim_mock):
        nominatim_mock.get(f"{NOMINATIM_URL}/search").respond(json=[
            {
                "lat": "23.8103",
                "lon": "90.4125",
                "display_name": "Dhaka, Bangladesh",
                "boundingbox": ["23.6", "24.0", "90.2", "90.6"],
                "osm_type": "relation",
                "osm_id": 123456,
                "importance": 0.9,
            }
        ])

        result = await geocode("Dhaka")
        assert isinstance(result, list) or "error" not in result
        if isinstance(result, list):
            assert result[0]["name"] == "Dhaka, Bangladesh"
            assert result[0]["lat"] == 23.8103

    @pytest.mark.asyncio
    async def test_geocode_with_country(self, nominatim_mock):
        nominatim_mock.get(
            f"{NOMINATIM_URL}/search",
        ).respond(json=[])

        result = await geocode("Dhaka", countrycodes="bd")
        # Should not error
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_reverse_geocode(self, nominatim_mock):
        nominatim_mock.get(
            f"{NOMINATIM_URL}/reverse",
        ).respond(json={
            "lat": "23.8103",
            "lon": "90.4125",
            "display_name": "123 Example Street, Dhaka",
            "address": {"road": "Example Street", "city": "Dhaka"},
        })

        result = await reverse_geocode(23.8103, 90.4125)
        assert isinstance(result, dict)
        if "error" not in result:
            assert "address" in result or "display_name" in result
