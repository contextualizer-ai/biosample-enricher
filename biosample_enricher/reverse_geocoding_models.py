"""
Pydantic models for reverse geocoding data normalization and validation.

Provides explicit schema definitions for standardized reverse geocoding results
from OSM and Google providers.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AddressComponentType(str, Enum):
    """Types of address components from various providers."""

    # Common administrative levels
    COUNTRY = "country"
    ADMINISTRATIVE_AREA_LEVEL_1 = "administrative_area_level_1"  # State/Province
    ADMINISTRATIVE_AREA_LEVEL_2 = "administrative_area_level_2"  # County
    ADMINISTRATIVE_AREA_LEVEL_3 = "administrative_area_level_3"  # District
    ADMINISTRATIVE_AREA_LEVEL_4 = "administrative_area_level_4"  # Ward
    ADMINISTRATIVE_AREA_LEVEL_5 = "administrative_area_level_5"  # Sub-district

    # Locality types
    LOCALITY = "locality"  # City/Town
    SUBLOCALITY = "sublocality"  # Neighborhood
    SUBLOCALITY_LEVEL_1 = "sublocality_level_1"
    SUBLOCALITY_LEVEL_2 = "sublocality_level_2"
    SUBLOCALITY_LEVEL_3 = "sublocality_level_3"
    SUBLOCALITY_LEVEL_4 = "sublocality_level_4"
    SUBLOCALITY_LEVEL_5 = "sublocality_level_5"

    # Street/Route types
    ROUTE = "route"  # Street
    STREET_NUMBER = "street_number"
    STREET_ADDRESS = "street_address"
    PREMISE = "premise"  # Building
    SUBPREMISE = "subpremise"  # Unit/Apartment

    # Postal codes
    POSTAL_CODE = "postal_code"
    POSTAL_CODE_PREFIX = "postal_code_prefix"
    POSTAL_CODE_SUFFIX = "postal_code_suffix"

    # Geographic features
    NATURAL_FEATURE = "natural_feature"
    PARK = "park"
    POINT_OF_INTEREST = "point_of_interest"
    ESTABLISHMENT = "establishment"
    NEIGHBORHOOD = "neighborhood"
    COLLOQUIAL_AREA = "colloquial_area"

    # Other
    PLUS_CODE = "plus_code"
    POLITICAL = "political"
    INTERSECTION = "intersection"
    CONTINENT = "continent"
    REGION = "region"
    ISLAND = "island"
    ARCHIPELAGO = "archipelago"


class AddressComponent(BaseModel):
    """Structured address component with type and value."""

    type: AddressComponentType = Field(description="Type of address component")
    short_name: str = Field(description="Short form of the component name")
    long_name: str | None = Field(
        default=None, description="Long form of the component name"
    )
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score for this component"
    )
    osm_id: str | None = Field(
        default=None, description="OpenStreetMap ID if available"
    )
    wikidata_id: str | None = Field(
        default=None, description="Wikidata ID if available"
    )


class BoundingBox(BaseModel):
    """Geographic bounding box."""

    north: float = Field(ge=-90, le=90, description="Northern latitude bound")
    south: float = Field(ge=-90, le=90, description="Southern latitude bound")
    east: float = Field(ge=-180, le=180, description="Eastern longitude bound")
    west: float = Field(ge=-180, le=180, description="Western longitude bound")


class PlaceType(str, Enum):
    """Types of places that can be returned."""

    BUILDING = "building"
    HOUSE = "house"
    AMENITY = "amenity"
    SHOP = "shop"
    TOURISM = "tourism"
    HISTORIC = "historic"
    LEISURE = "leisure"
    NATURAL = "natural"
    LANDUSE = "landuse"
    WATERWAY = "waterway"
    HIGHWAY = "highway"
    RAILWAY = "railway"
    AEROWAY = "aeroway"
    BOUNDARY = "boundary"
    PLACE = "place"
    OFFICE = "office"
    EMERGENCY = "emergency"
    MILITARY = "military"
    CRAFT = "craft"
    MAN_MADE = "man_made"
    ESTABLISHMENT = "establishment"
    POINT_OF_INTEREST = "point_of_interest"
    PARK = "park"
    OTHER = "other"


class ReverseGeocodeLocation(BaseModel):
    """Single reverse geocoding result location."""

    # Primary address information
    formatted_address: str = Field(description="Full formatted address string")
    display_name: str | None = Field(
        default=None, description="Display name (OSM style)"
    )

    # Structured address components
    components: list[AddressComponent] = Field(
        default_factory=list, description="Structured address components"
    )

    # Administrative hierarchy
    country: str | None = Field(default=None, description="Country name")
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-2 country code"
    )
    state: str | None = Field(default=None, description="State or province")
    state_code: str | None = Field(default=None, description="State code")
    county: str | None = Field(default=None, description="County or district")
    city: str | None = Field(default=None, description="City or town")
    suburb: str | None = Field(default=None, description="Suburb or neighborhood")
    postcode: str | None = Field(default=None, description="Postal code")

    # Street-level details
    road: str | None = Field(default=None, description="Road or street name")
    house_number: str | None = Field(default=None, description="House number")
    house_name: str | None = Field(default=None, description="House or building name")

    # Place information
    place_type: PlaceType | None = Field(default=None, description="Type of place")
    place_rank: int | None = Field(
        default=None, ge=0, le=30, description="OSM place rank (0-30)"
    )
    importance: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Importance score"
    )

    # Geographic details
    lat: float = Field(ge=-90, le=90, description="Latitude of result")
    lon: float = Field(ge=-180, le=180, description="Longitude of result")
    bounding_box: BoundingBox | None = Field(
        default=None, description="Bounding box of the place"
    )

    # External identifiers
    place_id: str | None = Field(default=None, description="Provider-specific place ID")
    osm_id: str | None = Field(default=None, description="OpenStreetMap ID")
    osm_type: str | None = Field(
        default=None, description="OpenStreetMap type (node/way/relation)"
    )
    wikidata_id: str | None = Field(default=None, description="Wikidata ID")
    wikipedia_url: str | None = Field(default=None, description="Wikipedia URL")

    # Additional metadata
    licence: str | None = Field(default=None, description="Data licence")
    attribution: str | None = Field(default=None, description="Data attribution")

    # Quality indicators
    distance_m: float | None = Field(
        default=None, description="Distance from query point in meters"
    )
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Overall confidence score"
    )


class ReverseGeocodeProvider(BaseModel):
    """Information about the reverse geocoding provider."""

    name: str = Field(description="Name of the provider")
    endpoint: str | None = Field(default=None, description="API endpoint URL")
    api_version: str | None = Field(default=None, description="API version")
    rate_limit: int | None = Field(
        default=None, description="Rate limit (requests per second)"
    )


class ReverseGeocodeResult(BaseModel):
    """Complete reverse geocoding result with metadata."""

    # Query information
    query_lat: float = Field(description="Query latitude")
    query_lon: float = Field(description="Query longitude")

    # Results
    locations: list[ReverseGeocodeLocation] = Field(
        description="List of geocoded locations, ordered by relevance"
    )

    # Provider information
    provider: ReverseGeocodeProvider = Field(description="Provider information")

    # Response metadata
    status: str = Field(description="Response status")
    error_message: str | None = Field(
        default=None, description="Error message if status is not OK"
    )
    response_time_ms: float | None = Field(
        default=None, description="Response time in milliseconds"
    )
    cache_hit: bool = Field(default=False, description="Whether result was from cache")

    # Timestamps
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the request"
    )

    # Raw response (for debugging)
    raw_response: dict[str, Any] | None = Field(
        default=None, description="Raw API response for debugging"
    )

    def get_best_match(self) -> ReverseGeocodeLocation | None:
        """Get the best matching location (first in list)."""
        return self.locations[0] if self.locations else None

    def get_country(self) -> str | None:
        """Get country from the best match."""
        best = self.get_best_match()
        return best.country if best else None

    def get_formatted_address(self) -> str | None:
        """Get formatted address from the best match."""
        best = self.get_best_match()
        return best.formatted_address if best else None

    def filter_by_type(self, place_type: PlaceType) -> list[ReverseGeocodeLocation]:
        """Filter locations by place type."""
        return [loc for loc in self.locations if loc.place_type == place_type]

    def to_simple_dict(self) -> dict[str, Any]:
        """Convert to simple dictionary for easy viewing."""
        best = self.get_best_match()
        if not best:
            return {
                "status": self.status,
                "error": self.error_message,
                "provider": self.provider.name,
            }

        return {
            "formatted_address": best.formatted_address,
            "country": best.country,
            "state": best.state,
            "city": best.city,
            "postcode": best.postcode,
            "coordinates": {"lat": best.lat, "lon": best.lon},
            "provider": self.provider.name,
            "confidence": best.confidence,
            "status": self.status,
        }


class ReverseGeocodeFetchResult(BaseModel):
    """Internal result from provider fetch operation."""

    ok: bool = Field(description="Whether the fetch was successful")
    result: ReverseGeocodeResult | None = Field(
        default=None, description="Reverse geocoding result"
    )
    error: str | None = Field(default=None, description="Error message if not ok")
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Raw provider response"
    )
