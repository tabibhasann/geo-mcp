"""Tests for configuration and settings."""



from geo_mcp import __version__
from geo_mcp.config import Settings


class TestSettings:
    def test_default_values(self):
        s = Settings()
        assert s.nominatim_url == "https://nominatim.openstreetmap.org"
        assert s.osrm_url == "https://router.project-osrm.org"
        assert s.overpass_url == "https://overpass-api.de/api/interpreter"
        assert s.geocode_result_limit == 5
        assert s.osm_result_limit == 200
        assert s.http_retries == 3
        assert s.dry_run is False
        assert s.quiet is False

    def test_env_prefix(self):
        s = Settings(_env_file=None, nominatim_url="https://custom.example.com")
        assert s.nominatim_url == "https://custom.example.com"

    def test_user_agent_contains_version(self):
        s = Settings()
        assert __version__ in s.user_agent

    def test_user_agent_contains_github(self):
        s = Settings()
        assert "github.com" in s.user_agent

    def test_provider_defaults(self):
        s = Settings()
        assert s.geocoding_provider == "nominatim"
        assert s.routing_provider == "osrm"
        assert s.elevation_provider == "open_elevation"

    def test_quota_defaults(self):
        s = Settings()
        assert s.nominatim_daily_limit == 0
        assert s.osrm_daily_limit == 0
        assert s.open_elevation_daily_limit == 0

    def test_extra_ignored(self):
        s = Settings(_env_file=None, extra="ignore")
        assert s.model_config["extra"] == "ignore"
