"""Data models for forward geocoding results (place names to coordinates)."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LocationType(str, Enum):
    """Types of locations that can be geocoded."""

    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    TOWN = "town"
    VILLAGE = "village"
    POSTAL_CODE = "postal_code"
    ADDRESS = "address"
    LANDMARK = "landmark"
    NATURAL_FEATURE = "natural_feature"
    ADMINISTRATIVE_AREA = "administrative_area"
    UNKNOWN = "unknown"


class GeometryType(str, Enum):
    """Types of geometry returned by geocoding services."""

    POINT = "POINT"
    BOUNDS = "BOUNDS"
    APPROXIMATE = "APPROXIMATE"
    INTERPOLATED = "INTERPOLATED"
    ROOFTOP = "ROOFTOP"


class BoundingBox(BaseModel):
    """Geographic bounding box for a location."""

    northeast_lat: float = Field(description="Northeast corner latitude")
    northeast_lon: float = Field(description="Northeast corner longitude")
    southwest_lat: float = Field(description="Southwest corner latitude")
    southwest_lon: float = Field(description="Southwest corner longitude")


class ForwardGeocodeLocation(BaseModel):
    """A geocoded location result (place name to coordinates)."""

    # Input query information
    input_query: str = Field(description="Original place name query")

    # Results
    formatted_address: str = Field(description="Formatted address from provider")
    display_name: str | None = Field(default=None, description="Primary display name")

    # Coordinates (the main output)
    latitude: float = Field(ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(ge=-180, le=180, description="Longitude coordinate")

    # Administrative components
    country: str | None = Field(default=None, description="Country name")
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-2 country code"
    )
    state: str | None = Field(default=None, description="State or province")
    state_code: str | None = Field(default=None, description="State/province code")
    county: str | None = Field(default=None, description="County")
    city: str | None = Field(default=None, description="City")
    postal_code: str | None = Field(default=None, description="Postal code")

    # Location metadata
    location_type: LocationType = Field(
        default=LocationType.UNKNOWN, description="Type of location"
    )
    geometry_type: GeometryType | None = Field(
        default=None, description="Precision of coordinates"
    )
    bounding_box: BoundingBox | None = Field(
        default=None, description="Bounding box if applicable"
    )

    # Quality indicators
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score"
    )
    relevance: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Relevance to query"
    )
    accuracy_m: float | None = Field(
        default=None, gt=0.0, description="Location accuracy in meters"
    )

    # External identifiers
    place_id: str | None = Field(default=None, description="Provider-specific place ID")
    osm_id: str | None = Field(default=None, description="OpenStreetMap ID")
    osm_type: str | None = Field(
        default=None, description="OSM type (node/way/relation)"
    )

    # Additional context
    importance: float | None = Field(default=None, description="Geographic importance")
    population: int | None = Field(default=None, description="Population if available")


class ForwardGeocodeProvider(BaseModel):
    """Information about the geocoding provider."""

    name: str = Field(description="Provider name")
    endpoint: str | None = Field(default=None, description="API endpoint")
    api_version: str | None = Field(default=None, description="API version")
    attribution: str | None = Field(default=None, description="Required attribution")


class ForwardGeocodeResult(BaseModel):
    """Complete forward geocoding result with metadata."""

    # Query information
    query: str = Field(description="Input place name query")
    query_type: str | None = Field(default=None, description="Type of query detected")

    # Results (ordered by relevance)
    locations: list[ForwardGeocodeLocation] = Field(
        default_factory=list, description="Geocoded locations ordered by relevance"
    )

    # Provider information
    provider: ForwardGeocodeProvider = Field(description="Provider details")

    # Response metadata
    status: str = Field(description="Response status (OK, ZERO_RESULTS, ERROR)")
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )
    response_time_ms: float | None = Field(
        default=None, description="Response time in milliseconds"
    )
    cache_hit: bool = Field(default=False, description="Whether result was cached")

    # Timestamps
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Request timestamp"
    )

    # Raw response for debugging
    raw_response: dict[str, Any] | None = Field(
        default=None, description="Raw API response"
    )

    def get_best_match(self) -> ForwardGeocodeLocation | None:
        """Get the highest relevance/confidence location result."""
        if not self.locations:
            return None

        # Sort by relevance first, then confidence
        best = max(
            self.locations,
            key=lambda loc: (
                loc.relevance or 0.0,
                loc.confidence or 0.0,
                -(
                    loc.accuracy_m or float("inf")
                ),  # Prefer higher accuracy (lower meters)
            ),
        )
        return best

    def get_coordinates(self) -> tuple[float, float] | None:
        """Get coordinates from best match."""
        best = self.get_best_match()
        return (best.latitude, best.longitude) if best else None

    def get_administrative_summary(self) -> dict[str, str]:
        """Get administrative components from best match."""
        best = self.get_best_match()
        if not best:
            return {}

        summary = {}
        if best.country:
            summary["country"] = best.country
        if best.country_code:
            summary["country_code"] = best.country_code
        if best.state:
            summary["state"] = best.state
        if best.county:
            summary["county"] = best.county
        if best.city:
            summary["city"] = best.city
        if best.postal_code:
            summary["postal_code"] = best.postal_code

        return summary

    def to_enrichment_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for biosample coordinate enrichment."""
        best = self.get_best_match()
        if not best:
            return {}

        enrichment: dict[str, Any] = {}

        # Core coordinates (the main output)
        enrichment["latitude"] = best.latitude
        enrichment["longitude"] = best.longitude

        # Administrative components
        admin_summary = self.get_administrative_summary()
        enrichment.update(admin_summary)

        # Location context
        enrichment["formatted_address"] = best.formatted_address
        if best.location_type != LocationType.UNKNOWN:
            enrichment["location_type"] = best.location_type.value
        if best.geometry_type:
            enrichment["geometry_type"] = best.geometry_type.value

        # Quality metrics
        if best.confidence:
            enrichment["geocoding_confidence"] = best.confidence
        if best.relevance:
            enrichment["geocoding_relevance"] = best.relevance
        if best.accuracy_m:
            enrichment["coordinate_accuracy_m"] = best.accuracy_m

        # Provider information
        enrichment["geocoding_provider"] = self.provider.name
        enrichment["geocoding_query"] = self.query

        return enrichment


class ForwardGeocodeFetchResult(BaseModel):
    """Internal result from provider fetch operation."""

    ok: bool = Field(description="Whether fetch was successful")
    result: ForwardGeocodeResult | None = Field(
        default=None, description="Geocoding result"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Raw provider response"
    )
