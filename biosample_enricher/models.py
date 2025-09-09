"""Data models for biosample metadata."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BiosampleMetadata(BaseModel):
    """Model for biosample metadata."""

    model_config = ConfigDict(extra="allow", validate_assignment=True)

    sample_id: str = Field(..., description="Unique identifier for the biosample")
    sample_name: str | None = Field(None, description="Human-readable name")
    organism: str | None = Field(None, description="Source organism")
    tissue_type: str | None = Field(None, description="Type of tissue")
    collection_date: str | None = Field(None, description="Date of collection")
    location: str | None = Field(None, description="Geographic location")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    enriched_data: dict[str, Any] = Field(
        default_factory=dict, description="AI-enriched metadata"
    )


class EnrichmentResult(BaseModel):
    """Result of enrichment process."""

    model_config = ConfigDict(extra="forbid")

    original_metadata: BiosampleMetadata
    enriched_metadata: BiosampleMetadata
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in enrichment"
    )
    sources: list[str] = Field(default_factory=list, description="Data sources used")
    processing_time: float = Field(..., description="Processing time in seconds")
