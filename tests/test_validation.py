"""Tests for input validation utilities."""

import pytest

from geo_mcp.validation import (
    validate_bbox,
    validate_coords,
    validate_lat,
    validate_lon,
    validate_non_negative,
    validate_positive,
)


class TestValidateLat:
    def test_valid_lat(self):
        validate_lat(0.0)
        validate_lat(90.0)
        validate_lat(-90.0)
        validate_lat(45.5)

    def test_invalid_lat_too_high(self):
        with pytest.raises(ValueError, match="must be between -90 and 90"):
            validate_lat(90.1)

    def test_invalid_lat_too_low(self):
        with pytest.raises(ValueError, match="must be between -90 and 90"):
            validate_lat(-90.1)

    def test_custom_name(self):
        with pytest.raises(ValueError, match="south"):
            validate_lat(-91, name="south")


class TestValidateLon:
    def test_valid_lon(self):
        validate_lon(0.0)
        validate_lon(180.0)
        validate_lon(-180.0)
        validate_lon(123.45)

    def test_invalid_lon_too_high(self):
        with pytest.raises(ValueError, match="must be between -180 and 180"):
            validate_lon(180.1)

    def test_invalid_lon_too_low(self):
        with pytest.raises(ValueError, match="must be between -180 and 180"):
            validate_lon(-180.1)


class TestValidateCoords:
    def test_valid_coords(self):
        validate_coords(0.0, 0.0)
        validate_coords(180.0, 90.0)
        validate_coords(-180.0, -90.0)

    def test_invalid_lat_raises(self):
        with pytest.raises(ValueError):
            validate_coords(0.0, 91.0)

    def test_invalid_lon_raises(self):
        with pytest.raises(ValueError):
            validate_coords(181.0, 0.0)


class TestValidateBbox:
    def test_valid_bbox(self):
        validate_bbox([23.7, 90.3, 23.9, 90.5])

    def test_wrong_length(self):
        with pytest.raises(ValueError, match="4 values"):
            validate_bbox([1, 2, 3])

    def test_south_greater_than_north(self):
        with pytest.raises(ValueError, match="south.*must be less than north"):
            validate_bbox([50, 0, 40, 10])

    def test_invalid_lat_in_bbox(self):
        with pytest.raises(ValueError):
            validate_bbox([91, 0, 92, 10])


class TestValidatePositive:
    def test_valid_positive(self):
        validate_positive(1, "value")
        validate_positive(0.001, "value")

    def test_zero_rejected(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive(0, "value")

    def test_negative_rejected(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive(-1, "value")


class TestValidateNonNegative:
    def test_valid_non_negative(self):
        validate_non_negative(0, "value")
        validate_non_negative(1, "value")
        validate_non_negative(0.001, "value")

    def test_negative_rejected(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            validate_non_negative(-0.001, "value")
