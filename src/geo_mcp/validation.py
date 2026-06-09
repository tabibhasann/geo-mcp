"""Input validation utilities for geospatial parameters."""


def validate_lat(lat: float, name: str = "lat") -> None:
    """Validate latitude is within valid range [-90, 90]."""
    if not -90 <= lat <= 90:
        raise ValueError(f"{name} must be between -90 and 90, got {lat}")


def validate_lon(lon: float, name: str = "lon") -> None:
    """Validate longitude is within valid range [-180, 180]."""
    if not -180 <= lon <= 180:
        raise ValueError(f"{name} must be between -180 and 180, got {lon}")


def validate_coords(lon: float, lat: float) -> None:
    """Validate a coordinate pair."""
    validate_lon(lon)
    validate_lat(lat)


def validate_bbox(bbox: list[float]) -> None:
    """Validate a bounding box [south, west, north, east]."""
    if len(bbox) != 4:
        raise ValueError("bbox must be [south, west, north, east] with 4 values")
    south, west, north, east = bbox
    validate_lat(south, "south")
    validate_lat(north, "north")
    validate_lon(west, "west")
    validate_lon(east, "east")
    if south > north:
        raise ValueError(f"south ({south}) must be less than north ({north})")


def validate_positive(value: float, name: str) -> None:
    """Validate a value is positive."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_non_negative(value: float, name: str) -> None:
    """Validate a value is non-negative."""
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")
