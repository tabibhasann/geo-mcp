"""Tests for unit conversions and geodesic calculations."""

import pytest

from geo_mcp.units import (
    convert_area,
    convert_length,
    geodesic_area,
    geojson_to_shapely,
    parse_geojson,
    pick_utm_epsg,
)


class TestUnitConversions:
    def test_length_km(self):
        assert convert_length(1000, "m", "km") == 1.0

    def test_length_mi(self):
        assert convert_length(1000, "m", "mi") == pytest.approx(0.621371, rel=0.01)

    def test_area_km2(self):
        assert convert_area(1_000_000, "m2", "km2") == 1.0

    def test_area_ha(self):
        assert convert_area(10_000, "m2", "ha") == 1.0

    def test_area_acre(self):
        assert convert_area(1_000_000, "m2", "acre") > 200

    def test_unknown_length_unit(self):
        with pytest.raises(ValueError, match="Unknown length unit"):
            convert_length(100, "m", "furlong")

    def test_unknown_area_unit(self):
        with pytest.raises(ValueError, match="Unknown area unit"):
            convert_area(100, "m2", "barn")


class TestUTMZone:
    def test_bangladesh_utm(self):
        import shapely

        geom = shapely.from_wkt("POINT(90.4 23.8)")
        epsg = pick_utm_epsg(geom)
        assert epsg.startswith("EPSG:326"), f"Northern hemisphere should be 326xx, got {epsg}"

    def test_jakarta_utm(self):
        import shapely

        geom = shapely.from_wkt("POINT(106.8 -6.2)")
        epsg = pick_utm_epsg(geom)
        assert epsg.startswith("EPSG:327"), f"Southern hemisphere should be 327xx, got {epsg}"

    def test_london_utm(self):
        import shapely

        geom = shapely.from_wkt("POINT(-0.1 51.5)")
        epsg = pick_utm_epsg(geom)
        assert epsg == "EPSG:32630"

    def test_los_angeles_utm(self):
        import shapely

        geom = shapely.from_wkt("POINT(-118.2 34.0)")
        epsg = pick_utm_epsg(geom)
        assert epsg == "EPSG:32611"


class TestGeodesicArea:
    def test_1deg_box_near_equator(self):
        import shapely

        geom = shapely.from_wkt("POLYGON((90 0, 91 0, 91 1, 90 1, 90 0))")
        area_km2 = geodesic_area(geom, "km2")
        assert 10000 < area_km2 < 15000

    def test_point_zero_area(self):
        import shapely

        geom = shapely.from_wkt("POINT(90 23)")
        assert geodesic_area(geom) == 0.0


class TestParse:
    def test_parse_str(self):
        data = parse_geojson('{"type":"Point","coordinates":[1,2]}')
        assert data["type"] == "Point"

    def test_parse_bad(self):
        with pytest.raises(ValueError):
            parse_geojson("not json")

    def test_to_shapely(self):
        geom = geojson_to_shapely('{"type":"Point","coordinates":[1,2]}')
        assert geom.geom_type == "Point"
