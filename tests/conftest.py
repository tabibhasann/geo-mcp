"""Shared test fixtures for mcp-geo tests."""

import json

import pytest


@pytest.fixture
def point_geojson() -> str:
    return json.dumps(
        {
            "type": "Point",
            "coordinates": [90.4125, 23.8103],
        }
    )


@pytest.fixture
def polygon_geojson() -> str:
    """A 1°×1° box near the equator (approximately 111 km × 111 km)."""
    return json.dumps(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [90.0, 0.0],
                    [91.0, 0.0],
                    [91.0, 1.0],
                    [90.0, 1.0],
                    [90.0, 0.0],
                ]
            ],
        }
    )


@pytest.fixture
def small_polygon_geojson() -> str:
    """A small (~100m) square polygon for buffer tests."""
    return json.dumps(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [90.4120, 23.8100],
                    [90.4130, 23.8100],
                    [90.4130, 23.8110],
                    [90.4120, 23.8110],
                    [90.4120, 23.8100],
                ]
            ],
        }
    )


@pytest.fixture
def multipoint_geojson() -> str:
    return json.dumps(
        {
            "type": "MultiPoint",
            "coordinates": [
                [90.4125, 23.8103],
                [90.4150, 23.8120],
            ],
        }
    )


@pytest.fixture
def linestring_geojson() -> str:
    return json.dumps(
        {
            "type": "LineString",
            "coordinates": [
                [90.0, 0.0],
                [91.0, 0.0],
                [91.0, 1.0],
            ],
        }
    )
