"""Provider plugin system for geocoding, routing, and elevation.

Each provider implements a simple ABC.  The active provider is selected via
environment variables (GEO_MCP_GEOCODING_PROVIDER, GEO_MCP_ROUTING_PROVIDER,
GEO_MCP_ELEVATION_PROVIDER).  Defaults are Nominatim, OSRM, and
Open-Elevation respectively — all free, no API key required.

To add a new provider (e.g. Mapbox, Google), subclass the relevant ABC and
register it in the PROVIDER_REGISTRY below.
"""

from __future__ import annotations

from ..config import settings
from .base import (
    ElevationProvider,
    GeocodingProvider,
    RoutingProvider,
)
from .base import (
    MockData as MockData,
)
from .base import (
    QuotaTracker as QuotaTracker,
)
from .base import (
    get_quota_tracker as get_quota_tracker,
)
from .base import (
    is_dry_run as is_dry_run,
)
from .elevation import OpenElevationProvider
from .geocoding import NominatimProvider
from .routing import OSRMProvider

PROVIDER_REGISTRY: dict[str, dict[str, type]] = {
    "geocoding": {
        "nominatim": NominatimProvider,
    },
    "routing": {
        "osrm": OSRMProvider,
    },
    "elevation": {
        "open_elevation": OpenElevationProvider,
    },
}


def get_geocoding_provider() -> GeocodingProvider:
    name = getattr(settings, "geocoding_provider", "nominatim")
    cls = PROVIDER_REGISTRY["geocoding"].get(name)
    if cls is None:
        raise ValueError(
            f"Unknown geocoding provider '{name}'. "
            f"Available: {sorted(PROVIDER_REGISTRY['geocoding'])}"
        )
    return cls()  # type: ignore[no-any-return]


def get_routing_provider() -> RoutingProvider:
    name = getattr(settings, "routing_provider", "osrm")
    cls = PROVIDER_REGISTRY["routing"].get(name)
    if cls is None:
        raise ValueError(
            f"Unknown routing provider '{name}'. "
            f"Available: {sorted(PROVIDER_REGISTRY['routing'])}"
        )
    return cls()  # type: ignore[no-any-return]


def get_elevation_provider() -> ElevationProvider:
    name = getattr(settings, "elevation_provider", "open_elevation")
    cls = PROVIDER_REGISTRY["elevation"].get(name)
    if cls is None:
        raise ValueError(
            f"Unknown elevation provider '{name}'. "
            f"Available: {sorted(PROVIDER_REGISTRY['elevation'])}"
        )
    return cls()  # type: ignore[no-any-return]


def list_providers() -> dict:
    """Return all registered providers grouped by service type."""
    return {
        service: {
            name: {"class": cls.__name__, "module": cls.__module__}
            for name, cls in providers.items()
        }
        for service, providers in PROVIDER_REGISTRY.items()
    }
