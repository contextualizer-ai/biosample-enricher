"""
Pydantic models for biosample data normalization and validation.

Provides explicit schema definitions for standardized biosample location data
extracted from NMDC and GOLD databases.
"""

from datetime import datetime

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
