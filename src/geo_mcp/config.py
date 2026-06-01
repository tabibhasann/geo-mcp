"""Configuration via environment variables and sensible defaults."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configurable settings for mcp-geo."""

    model_config = {"env_prefix": "GEO_MCP_", "env_file": ".env", "extra": "ignore"}

    nominatim_url: str = "https://nominatim.openstreetmap.org"
    osrm_url: str = "https://router.project-osrm.org"
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    user_agent: str = "geo-mcp/0.1.0 (OSS MCP server; github.com/tabibhasann/geo-mcp)"

    nominatim_rate_limit: float = 1.0  # requests per second
    overpass_timeout: float = 30.0

    geocode_result_limit: int = 5
    osm_result_limit: int = 200


settings = Settings()
