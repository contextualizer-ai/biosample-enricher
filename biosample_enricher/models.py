"""
Pydantic models for biosample data normalization and validation.

Provides explicit schema definitions for standardized biosample location data
extracted from NMDC and GOLD databases, and elevation service output models.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class BiosampleLocation(BaseModel):
    """Standardized biosample location data for API enrichment."""

    # Required fields for API enrichment
    latitude: float | None = Field(
        None, ge=-90, le=90, description="Latitude in decimal degrees"
    )
    longitude: float | None = Field(
        None, ge=-180, le=180, description="Longitude in decimal degrees"
    )
    collection_date: str | None = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Collection date in YYYY-MM-DD format",
    )

    # Location context
    textual_location: str | None = Field(
        None, description="Human-readable location description"
    )

    # Source metadata and IDs
    sample_id: str | None = Field(None, description="Primary ID in native format")
    database_source: str | None = Field(
        None, pattern=r"^(NMDC|GOLD)$", description="Source database"
    )
    extraction_timestamp: str | None = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="When this record was extracted",
    )

    # Normalized ID fields
    nmdc_biosample_id: str | None = Field(None, description="Main NMDC ID")
    gold_biosample_id: str | None = Field(None, description="Main GOLD ID")
    alternative_identifiers: list[str] | None = Field(
        None, description="Alternative IDs"
    )
    external_database_identifiers: list[str] | None = Field(
        None, description="External database IDs"
    )
    biosample_identifiers: list[str] | None = Field(
        None, description="Biosample-specific IDs"
    )
    sample_identifiers: list[str] | None = Field(None, description="Sample IDs")

    # Associated studies
    nmdc_studies: list[str] | None = Field(None, description="NMDC associated_studies")
    gold_studies: list[str] | None = Field(
        None, description="GOLD seq_projects relationship"
    )

    # Quality indicators
    coordinate_precision: int | None = Field(
        None, ge=0, description="Decimal places in coordinates"
    )
    date_precision: str | None = Field(
        None, pattern=r"^(day|month|year)$", description="Date precision level"
    )
    location_completeness: float | None = Field(
        None, ge=0.0, le=1.0, description="Completeness score 0.0-1.0"
    )

    @model_validator(mode="after")
    def calculate_completeness(self) -> "BiosampleLocation":
        """Calculate location completeness score based on available fields."""
        required_fields = [
            self.latitude,
            self.longitude,
            self.collection_date,
            self.textual_location,
        ]
        available_fields = sum(1 for field in required_fields if field is not None)
        # Use object.__setattr__ to bypass Pydantic validation and avoid recursion
        object.__setattr__(
            self, "location_completeness", available_fields / len(required_fields)
        )
        return self

    @field_validator("collection_date")
    @classmethod
    def validate_collection_date(cls, v: str | None) -> str | None:
        """Validate collection date format."""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError("collection_date must be in YYYY-MM-DD format") from e

    def is_enrichable(self) -> bool:
        """Check if sample has minimum data for API enrichment."""
        return (
            self.latitude is not None
            and self.longitude is not None
            and -90 <= self.latitude <= 90
            and -180 <= self.longitude <= 180
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization with enrichable status."""
        data = self.model_dump()
        data["is_enrichable"] = self.is_enrichable()
        return data

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Prevent extra fields
        validate_assignment = True  # Validate on field assignment
        str_strip_whitespace = True  # Strip whitespace from strings


# Elevation Service Models


class Variable(str, Enum):
    """Enumeration of variables that can be observed/measured."""

    ELEVATION = "elevation"


class ValueStatus(str, Enum):
    """Status of the observation value."""

    OK = "ok"
    ERROR = "error"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class GeoPoint(BaseModel):
    """Geographic point with precision information."""

    lat: float = Field(description="Latitude in decimal degrees")
    lon: float = Field(description="Longitude in decimal degrees")
    precision_digits: int | None = Field(
        default=None, description="Number of decimal digits of precision"
    )
    uncertainty_m: float | None = Field(
        default=None, description="Uncertainty in meters"
    )


class ProviderRef(BaseModel):
    """Reference to a data provider."""

    name: str = Field(description="Name of the provider")
    endpoint: str | None = Field(default=None, description="API endpoint URL")
    api_version: str | None = Field(default=None, description="Version of the API used")


class Observation(BaseModel):
    """A single observation/measurement result."""

    variable: Variable = Field(description="The variable being observed")
    value_numeric: float | None = Field(
        default=None, description="Numeric value of the observation"
    )
    unit_ucum: str = Field(default="m", description="Unit of measure in UCUM format")
    value_status: ValueStatus = Field(
        default=ValueStatus.OK, description="Status of the observation value"
    )
    provider: ProviderRef = Field(description="Provider that made this observation")
    request_location: GeoPoint = Field(description="Location requested for observation")
    measurement_location: GeoPoint | None = Field(
        default=None, description="Actual location where measurement was taken"
    )
    distance_to_input_m: float | None = Field(
        default=None,
        description="Distance from request to measurement location in meters",
    )
    spatial_resolution_m: float | None = Field(
        default=None, description="Spatial resolution of the measurement in meters"
    )
    vertical_datum: str | None = Field(
        default=None, description="Vertical datum used for elevation measurements"
    )
    raw_payload: str | None = Field(
        default=None, description="Raw response from the provider"
    )
    raw_payload_sha256: str | None = Field(
        default=None, description="SHA-256 hash of the raw payload"
    )
    normalization_version: str = Field(
        description="Version of the normalization rules used"
    )
    cache_used: bool | None = Field(
        default=None, description="Whether this result came from cache"
    )
    request_id: str | None = Field(
        default=None, description="Unique identifier for this request"
    )
    error_message: str | None = Field(
        default=None, description="Error message if value_status is error"
    )
    created_at: datetime | None = Field(
        default=None, description="When this observation was created"
    )


class EnrichmentRun(BaseModel):
    """Metadata about a specific enrichment run."""

    started_at: datetime = Field(description="When the enrichment run started")
    ended_at: datetime | None = Field(
        default=None, description="When the enrichment run ended"
    )
    tool_version: str | None = Field(
        default=None, description="Version of the enrichment tool"
    )
    git_sha: str | None = Field(
        default=None, description="Git commit SHA of the tool version"
    )
    read_from_cache: bool | None = Field(
        default=None, description="Whether cached results were used"
    )
    write_to_cache: bool | None = Field(
        default=None, description="Whether results were written to cache"
    )


class OutputEnvelope(BaseModel):
    """Top-level container for enrichment results."""

    schema_version: str = Field(description="Version of the output schema")
    run: EnrichmentRun = Field(description="Information about the enrichment run")
    subject_id: str = Field(description="Identifier for the subject being enriched")
    observations: list[Observation] = Field(
        description="List of observations made during enrichment"
    )


class CoordinateClassification(BaseModel):
    """Classification of geographic coordinates."""

    is_us_territory: bool = Field(description="Whether coordinates are in US territory")
    is_land: bool | None = Field(
        default=None, description="Whether coordinates are on land (Phase 2+)"
    )
    country_code: str | None = Field(default=None, description="ISO country code")
    region: str | None = Field(
        default=None, description="Region code (CONUS, AK, HI, PR, GU, etc.)"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score for classification"
    )


class ElevationRequest(BaseModel):
    """Request for elevation data at specific coordinates."""

    latitude: float = Field(ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(
        ge=-180, le=180, description="Longitude in decimal degrees"
    )
    preferred_providers: list[str] | None = Field(
        default=None, description="Preferred providers in order of preference"
    )


class ElevationResult(BaseModel):
    """Single elevation result for compatibility/convenience."""

    latitude: float = Field(description="Latitude in decimal degrees")
    longitude: float = Field(description="Longitude in decimal degrees")
    elevation_meters: float = Field(description="Elevation in meters")
    provider: str = Field(description="Provider name")
    accuracy_meters: float | None = Field(
        default=None, description="Accuracy in meters"
    )
    data_source: str = Field(description="Data source identifier")
    timestamp: datetime = Field(description="When the measurement was taken")
    classification: CoordinateClassification = Field(
        description="Coordinate classification"
    )


class FetchResult(BaseModel):
    """Internal result from provider fetch operation."""

    ok: bool = Field(description="Whether the fetch was successful")
    elevation: float | None = Field(default=None, description="Elevation value")
    location: GeoPoint | None = Field(
        default=None, description="Location returned by provider"
    )
    resolution_m: float | None = Field(
        default=None, description="Spatial resolution in meters"
    )
    vertical_datum: str | None = Field(default=None, description="Vertical datum")
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Raw provider response"
    )
    error: str | None = Field(default=None, description="Error message if not ok")
