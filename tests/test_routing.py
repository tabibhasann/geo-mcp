"""Tests for OSRM routing client (mocked)."""

import json

import pytest
from respx import MockRouter

from geo_mcp.config import settings
from geo_mcp.routing import nearest_road, route, route_matrix

OSRM_URL = settings.osrm_url


@pytest.fixture
def osrm_mock(respx_mock: MockRouter):
    return respx_mock


class TestRoute:
    @pytest.mark.asyncio
    async def test_route_success(self, osrm_mock):
        osrm_mock.get(url__regex=r".*/route/v1/driving/.*").respond(json={
            "code": "Ok",
            "routes": [{
                "distance": 5000.0,
                "duration": 600.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[90.4, 23.8], [90.5, 23.9]],
                },
            }],
        })

        coords = json.dumps([[90.4, 23.8], [90.5, 23.9]])
        result = await route(coords)
        assert isinstance(result, dict)
        if "error" not in result:
            assert result["distance_m"] == 5000.0

    @pytest.mark.asyncio
    async def test_invalid_profile(self):
        coords = json.dumps([[0, 0], [1, 1]])
        result = await route(coords, profile="flying")
        assert "error" in result


class TestRouteMatrix:
    @pytest.mark.asyncio
    async def test_matrix_success(self, osrm_mock):
        osrm_mock.get(url__regex=r".*/table/v1/.*").respond(json={
            "code": "Ok",
            "durations": [[0, 100], [100, 0]],
            "distances": [[0, 5000], [5000, 0]],
        })

        sources = json.dumps([[90.4, 23.8]])
        dests = json.dumps([[90.5, 23.9]])
        result = await route_matrix(sources, dests)
        assert isinstance(result, dict)
        if "error" not in result:
            assert "durations" in result


class TestNearestRoad:
    @pytest.mark.asyncio
    async def test_nearest_success(self, osrm_mock):
        osrm_mock.get(url__regex=r".*/nearest/v1/.*").respond(json={
            "code": "Ok",
            "waypoints": [{
                "location": [90.4125, 23.8103],
                "name": "Main Street",
                "distance": 5.0,
            }],
        })

        result = await nearest_road(23.8103, 90.4125)
        assert isinstance(result, dict)
        if "error" not in result:
            assert result["name"] == "Main Street"
