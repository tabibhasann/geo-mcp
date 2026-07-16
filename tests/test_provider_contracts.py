"""Provider contract tests using recorded fixture responses.

These tests verify that each provider correctly parses the response format
of its upstream API and returns the expected mcp-geo result shape.
All tests are network-free — they use respx mocks or unittest.mock patches
to replay recorded API responses.
"""

import json

import pytest
from respx import MockRouter

from geo_mcp.config import settings
from geo_mcp.elevation import elevation, elevation_profile
from geo_mcp.geocoding import geocode, reverse_geocode
from geo_mcp.isochrones import isochrone
from geo_mcp.osm import overpass_query
from geo_mcp.routing import nearest_road, route, route_matrix

NOMINATIM_URL = settings.nominatim_url
OSRM_URL = settings.osrm_url
OVERPASS_URL = settings.overpass_url


# ─── Nominatim geocoding contract ──────────────────────────────────────────


class TestNominatimContract:
    """Verify NominatimProvider correctly parses Nominatim API responses."""

    @pytest.mark.asyncio
    async def test_geocode_parses_jsonv2_response(self, respx_mock: MockRouter):
        """Geocode returns normalized dicts from Nominatim jsonv2 format."""
        respx_mock.get(f"{NOMINATIM_URL}/search").respond(
            json=[
                {
                    "lat": "52.5163",
                    "lon": "13.3777",
                    "display_name": "Brandenburg Gate, Berlin, Germany",
                    "boundingbox": ["52.5151", "52.5175", "13.3765", "13.3789"],
                    "osm_type": "relation",
                    "osm_id": 123456,
                    "importance": 0.8,
                    "type": "tourism",
                }
            ]
        )
        result = await geocode("Brandenburg Gate, Berlin")
        assert isinstance(result, list)
        assert len(result) == 1
        r = result[0]
        assert r["lat"] == 52.5163
        assert r["lon"] == 13.3777
        assert r["name"] == "Brandenburg Gate, Berlin, Germany"
        assert r["bbox"] == [13.3765, 52.5151, 13.3789, 52.5175]
        assert r["osm_type"] == "relation"
        assert r["osm_id"] == 123456
        assert r["importance"] == 0.8

    @pytest.mark.asyncio
    async def test_geocode_empty_results(self, respx_mock: MockRouter):
        """Geocode returns empty list when Nominatim has no matches."""
        respx_mock.get(f"{NOMINATIM_URL}/search").respond(json=[])
        result = await geocode("Nonexistent Place XYZ123")
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_geocode_multiple_results_respects_limit(self, respx_mock: MockRouter):
        """Geocode respects the limit parameter."""
        respx_mock.get(f"{NOMINATIM_URL}/search").respond(
            json=[
                {"lat": "1.0", "lon": "2.0", "display_name": "A", "boundingbox": ["0", "1", "2", "3"],
                 "importance": 0.5},
                {"lat": "3.0", "lon": "4.0", "display_name": "B", "boundingbox": ["2", "3", "4", "5"],
                 "importance": 0.4},
                {"lat": "5.0", "lon": "6.0", "display_name": "C", "boundingbox": ["4", "5", "6", "7"],
                 "importance": 0.3},
            ]
        )
        result = await geocode("test", limit=2)
        assert isinstance(result, list)
        # The provider sends limit to the API; the mock returns all 3.
        # Verify the limit parameter was sent in the request.
        request = respx_mock.calls.last.request
        assert request.url.params.get("limit") == "2"

    @pytest.mark.asyncio
    async def test_reverse_geocode_parses_response(self, respx_mock: MockRouter):
        """Reverse geocode returns normalized dict from Nominatim reverse API."""
        respx_mock.get(f"{NOMINATIM_URL}/reverse").respond(
            json={
                "lat": "23.8103",
                "lon": "90.4125",
                "display_name": "123 Example Street, Dhaka, Bangladesh",
                "address": {"road": "Example Street", "city": "Dhaka", "country": "Bangladesh"},
                "osm_type": "node",
                "osm_id": 789,
            }
        )
        result = await reverse_geocode(23.8103, 90.4125)
        assert isinstance(result, dict)
        assert result["display_name"] == "123 Example Street, Dhaka, Bangladesh"
        assert result["address"]["city"] == "Dhaka"
        assert result["lat"] == 23.8103
        assert result["lon"] == 90.4125

    @pytest.mark.asyncio
    async def test_geocode_server_error_returns_error(self, respx_mock: MockRouter):
        """Geocode handles 5xx errors gracefully."""
        respx_mock.get(f"{NOMINATIM_URL}/search").respond(status_code=503)
        result = await geocode("test")
        assert isinstance(result, (list, dict))
        if isinstance(result, dict):
            assert "error" in result


# ─── OSRM routing contract ─────────────────────────────────────────────────


class TestOSRMContract:
    """Verify OSRMProvider correctly parses OSRM API responses."""

    @pytest.mark.asyncio
    async def test_route_parses_geojson_geometry(self, respx_mock: MockRouter):
        """Route returns distance, duration, and GeoJSON geometry from OSRM."""
        respx_mock.get(url__regex=r".*/route/v1/driving/.*").respond(
            json={
                "code": "Ok",
                "routes": [
                    {
                        "distance": 12500.0,
                        "duration": 900.0,
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[90.41, 23.81], [90.42, 23.82]],
                        },
                    }
                ],
            }
        )
        result = await route(json.dumps([[90.41, 23.81], [90.42, 23.82]]))
        assert isinstance(result, dict)
        assert result["distance_m"] == 12500.0
        assert result["duration_s"] == 900.0
        assert result["geometry"]["type"] == "LineString"
        assert result["geometry"]["coordinates"] == [[90.41, 23.81], [90.42, 23.82]]

    @pytest.mark.asyncio
    async def test_route_error_code(self, respx_mock: MockRouter):
        """Route handles OSRM non-Ok code responses."""
        respx_mock.get(url__regex=r".*/route/v1/driving/.*").respond(
            json={"code": "InvalidUrl", "message": "Bad coordinates"}
        )
        result = await route(json.dumps([[0, 0], [1, 1]]))
        assert isinstance(result, dict)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_route_matrix_parses_durations(self, respx_mock: MockRouter):
        """Route matrix returns durations and distances from OSRM table API."""
        respx_mock.get(url__regex=r".*/table/v1/.*").respond(
            json={
                "code": "Ok",
                "durations": [[0, 100], [100, 0]],
                "distances": [[0, 5000], [5000, 0]],
            }
        )
        result = await route_matrix(
            json.dumps([[90.4, 23.8]]),
            json.dumps([[90.5, 23.9]]),
        )
        assert isinstance(result, dict)
        assert result["durations"] == [[0, 100], [100, 0]]
        assert result["distances"] == [[0, 5000], [5000, 0]]

    @pytest.mark.asyncio
    async def test_nearest_road_parses_waypoint(self, respx_mock: MockRouter):
        """Nearest road returns location and name from OSRM nearest API."""
        respx_mock.get(url__regex=r".*/nearest/v1/.*").respond(
            json={
                "code": "Ok",
                "waypoints": [
                    {
                        "location": [90.4125, 23.8103],
                        "name": "Main Street",
                        "distance": 5.0,
                    }
                ],
            }
        )
        result = await nearest_road(23.8103, 90.4125)
        assert isinstance(result, dict)
        assert result["lat"] == 23.8103
        assert result["lon"] == 90.4125
        assert result["name"] == "Main Street"
        assert result["distance_m"] == 5.0


# ─── Open-Elevation contract ───────────────────────────────────────────────


class TestOpenElevationContract:
    """Verify OpenElevationProvider correctly parses Open-Elevation API responses."""

    @pytest.mark.asyncio
    async def test_elevation_parses_results_array(self):
        """Elevation returns lat, lon, elevation_m from Open-Elevation API."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"latitude": 27.9881, "longitude": 86.9250, "elevation": 8848.0}
            ]
        }
        mock_response.raise_for_status = lambda: None

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "geo_mcp.providers.elevation.get_client",
                lambda: _mock_client(mock_response, "get"),
            )
            result = await elevation(27.9881, 86.9250)
        assert result["lat"] == 27.9881
        assert result["lon"] == 86.9250
        assert result["elevation_m"] == 8848.0

    @pytest.mark.asyncio
    async def test_elevation_profile_parses_multiple_points(self):
        """Elevation profile returns a list of elevation points."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"latitude": 27.98, "longitude": 86.92, "elevation": 5300.0},
                {"latitude": 27.99, "longitude": 86.93, "elevation": 7000.0},
                {"latitude": 28.00, "longitude": 86.94, "elevation": 8848.0},
            ]
        }
        mock_response.raise_for_status = lambda: None

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "geo_mcp.providers.elevation.get_client",
                lambda: _mock_client(mock_response, "post"),
            )
            result = await elevation_profile([[86.92, 27.98], [86.93, 27.99], [86.94, 28.00]])
        assert len(result) == 3
        assert result[0]["elevation_m"] == 5300.0
        assert result[2]["elevation_m"] == 8848.0

    @pytest.mark.asyncio
    async def test_elevation_empty_results(self):
        """Elevation handles empty results array gracefully (returns None elevation)."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = lambda: None

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "geo_mcp.providers.elevation.get_client",
                lambda: _mock_client(mock_response, "get"),
            )
            result = await elevation(0.0, 0.0)
        assert isinstance(result, dict)
        # Provider falls back to `or [data]` for empty results, returning None elevation
        assert result.get("elevation_m") is None


# ─── Overpass API contract ─────────────────────────────────────────────────


class TestOverpassContract:
    """Verify Overpass query execution correctly parses Overpass API responses."""

    @pytest.mark.asyncio
    async def test_overpass_query_parses_elements(self, respx_mock: MockRouter):
        """Overpass query converts elements to GeoJSON FeatureCollection."""
        respx_mock.post(OVERPASS_URL).respond(
            json={
                "elements": [
                    {
                        "type": "node",
                        "id": 123,
                        "lat": 23.8103,
                        "lon": 90.4125,
                        "tags": {"amenity": "hospital", "name": "Dhaka Medical"},
                    },
                    {
                        "type": "way",
                        "id": 456,
                        "center": {"lat": 23.8200, "lon": 90.4200},
                        "tags": {"amenity": "hospital", "name": "Square Hospital"},
                    },
                ]
            }
        )
        result = await overpass_query("[out:json];node[amenity=hospital];out;")
        assert isinstance(result, dict)
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 2
        assert result["features"][0]["geometry"]["type"] == "Point"
        assert result["features"][0]["geometry"]["coordinates"] == [90.4125, 23.8103]
        assert result["features"][0]["properties"]["name"] == "Dhaka Medical"
        assert result["features"][1]["geometry"]["coordinates"] == [90.4200, 23.8200]

    @pytest.mark.asyncio
    async def test_overpass_query_empty_elements(self, respx_mock: MockRouter):
        """Overpass query handles empty result set."""
        respx_mock.post(OVERPASS_URL).respond(json={"elements": []})
        result = await overpass_query("[out:json];node[nonexistent=tag];out;")
        assert isinstance(result, dict)
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 0
        assert result["metadata"]["total_elements"] == 0

    @pytest.mark.asyncio
    async def test_overpass_query_skips_null_geometry(self, respx_mock: MockRouter):
        """Overpass query filters out elements without geometry."""
        respx_mock.post(OVERPASS_URL).respond(
            json={
                "elements": [
                    {
                        "type": "node",
                        "id": 1,
                        "lat": 23.8,
                        "lon": 90.4,
                        "tags": {"name": "Has Geo"},
                    },
                    {
                        "type": "relation",
                        "id": 2,
                        "tags": {"name": "No Geo"},
                    },
                ]
            }
        )
        result = await overpass_query("[out:json];out;")
        assert len(result["features"]) == 1
        assert result["features"][0]["properties"]["name"] == "Has Geo"

    @pytest.mark.asyncio
    async def test_overpass_query_truncation_metadata(self, respx_mock: MockRouter):
        """Overpass query adds truncation metadata when results exceed limit."""
        elements = [
            {"type": "node", "id": i, "lat": 23.8, "lon": 90.4, "tags": {}}
            for i in range(300)
        ]
        respx_mock.post(OVERPASS_URL).respond(json={"elements": elements})
        result = await overpass_query("[out:json];out;", limit=50)
        assert result["metadata"]["total_elements"] == 300
        assert result["metadata"]["truncated"] is True
        assert "note" in result["metadata"]


# ─── OpenRouteService isochrone contract ───────────────────────────────────


class TestORSContract:
    """Verify isochrone correctly parses ORS API responses."""

    @pytest.mark.asyncio
    async def test_isochrone_parses_feature_collection(self):
        """Isochrone returns GeoJSON FeatureCollection from ORS."""
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0.1, 0], [0.1, 0.1], [0, 0.1], [0, 0]]],
                    },
                    "properties": {"value": 900, "center": [0.05, 0.05]},
                }
            ],
        }
        mock_response.raise_for_status = lambda: None

        with patch("geo_mcp.isochrones.settings") as mock_settings:
            mock_settings.ors_api_key = "test_key"
            mock_settings.ors_url = "https://api.openrouteservice.org"
            with patch("geo_mcp.isochrones.get_client") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                result = await isochrone(0.05, 0.05, range_value=900, range_type="time")
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 1
        assert result["features"][0]["geometry"]["type"] == "Polygon"
        assert result["metadata"]["center"] == [0.05, 0.05]
        assert result["metadata"]["range_value"] == 900
        assert result["metadata"]["unit"] == "seconds"

    @pytest.mark.asyncio
    async def test_isochrone_no_api_key_returns_error(self):
        """Isochrone fails clearly when ORS API key is not set."""
        from unittest.mock import patch

        with patch("geo_mcp.isochrones.settings") as mock_settings:
            mock_settings.ors_api_key = None
            result = await isochrone(40.0, -74.0)
        assert isinstance(result, dict)
        assert "error" in result
        assert "ORS_API_KEY" in result["error"] or "API key" in result["error"]


# ─── Dry-run mode contract ─────────────────────────────────────────────────


class TestDryRunContract:
    """Verify dry-run mode returns mock data for all network-dependent providers."""

    @pytest.mark.asyncio
    async def test_dry_run_geocode_returns_mock(self):
        from geo_mcp.config import settings

        original = settings.dry_run
        settings.dry_run = True
        try:
            result = await geocode("anywhere")
            assert isinstance(result, list)
            assert len(result) >= 1
            assert "lat" in result[0]
            assert "lon" in result[0]
        finally:
            settings.dry_run = original

    @pytest.mark.asyncio
    async def test_dry_run_reverse_geocode_returns_mock(self):
        from geo_mcp.config import settings

        original = settings.dry_run
        settings.dry_run = True
        try:
            result = await reverse_geocode(23.8, 90.4)
            assert isinstance(result, dict)
            assert "display_name" in result
        finally:
            settings.dry_run = original

    @pytest.mark.asyncio
    async def test_dry_run_route_returns_mock(self):
        from geo_mcp.config import settings

        original = settings.dry_run
        settings.dry_run = True
        try:
            result = await route(json.dumps([[90.41, 23.81], [90.42, 23.82]]))
            assert "distance_m" in result
            assert "duration_s" in result
            assert "geometry" in result
        finally:
            settings.dry_run = original

    @pytest.mark.asyncio
    async def test_dry_run_elevation_returns_mock(self):
        from geo_mcp.config import settings

        original = settings.dry_run
        settings.dry_run = True
        try:
            result = await elevation(23.81, 90.41)
            assert "elevation_m" in result
        finally:
            settings.dry_run = original


# ─── Helpers ───────────────────────────────────────────────────────────────


class _MockAsyncClient:
    """Minimal async context manager that returns a mock response."""

    def __init__(self, response, method):
        self._response = response
        self._method = method

    async def __aenter__(self):
        from unittest.mock import AsyncMock, MagicMock

        client = MagicMock()
        setattr(client, self._method, AsyncMock(return_value=self._response))
        return client

    async def __aexit__(self, *args):
        pass


def _mock_client(response, method):
    return _MockAsyncClient(response, method)
