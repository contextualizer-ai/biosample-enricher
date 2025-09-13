"""Data models for land cover and vegetation enrichment."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LandCoverObservation(BaseModel):
    """Land cover classification from a specific provider."""

    provider: str = Field(..., description="Data provider name")
    actual_location: dict[str, float] = Field(
        ..., description="Actual pixel/data location"
    )
    distance_m: float = Field(
        ..., ge=0.0, description="Distance from requested location (meters)"
    )
    actual_date: date | None = Field(None, description="Date of land cover data")
    temporal_offset_days: int | None = Field(
        None, description="Days offset from requested date"
    )

    # Classification data
    class_code: str | None = Field(None, description="Raw classification code")
    class_label: str | None = Field(None, description="Human-readable class label")
    classification_system: str | None = Field(
        None, description="Classification scheme name"
    )

    # Quality metrics
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence score"
    )
    resolution_m: float | None = Field(
        None, gt=0.0, description="Spatial resolution (meters)"
    )

    # Additional metadata
    dataset_version: str | None = Field(None, description="Dataset version/year")
    quality_flags: list[str] = Field(
        default_factory=list, description="Quality control flags"
    )

    @field_validator("actual_location")
    @classmethod
    def validate_location(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate location coordinates."""
        if "lat" not in v or "lon" not in v:
            raise ValueError("Location must contain 'lat' and 'lon' keys")

        lat, lon = v["lat"], v["lon"]
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

        return v


class VegetationObservation(BaseModel):
    """Vegetation indices from a specific provider."""

    provider: str = Field(..., description="Data provider name")
    actual_location: dict[str, float] = Field(
        ..., description="Actual pixel/data location"
    )
    distance_m: float = Field(
        ..., ge=0.0, description="Distance from requested location (meters)"
    )
    actual_date: date | None = Field(None, description="Date of vegetation data")
    temporal_offset_days: int | None = Field(
        None, description="Days offset from requested date"
    )

    # Vegetation indices
    ndvi: float | None = Field(
        None, ge=-1.0, le=1.0, description="Normalized Difference Vegetation Index"
    )
    evi: float | None = Field(
        None, ge=-1.0, le=1.0, description="Enhanced Vegetation Index"
    )
    lai: float | None = Field(None, ge=0.0, description="Leaf Area Index")
    fpar: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Fraction of Photosynthetically Active Radiation",
    )

    # Quality metrics
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence score"
    )
    resolution_m: float | None = Field(
        None, gt=0.0, description="Spatial resolution (meters)"
    )

    # Additional metadata
    composite_period: str | None = Field(
        None, description="Temporal composite period (e.g., '16-day')"
    )
    quality_flags: list[str] = Field(
        default_factory=list, description="Quality control flags"
    )

    @field_validator("actual_location")
    @classmethod
    def validate_location(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate location coordinates."""
        if "lat" not in v or "lon" not in v:
            raise ValueError("Location must contain 'lat' and 'lon' keys")

        lat, lon = v["lat"], v["lon"]
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

        return v


class LandResult(BaseModel):
    """Complete land cover and vegetation enrichment result."""

    # Request metadata
    requested_location: dict[str, float] = Field(
        ..., description="Originally requested coordinates"
    )
    requested_date: date | None = Field(None, description="Originally requested date")

    # Land cover results from all providers
    land_cover: list[LandCoverObservation] = Field(
        default_factory=list, description="Land cover classifications"
    )

    # Vegetation index results from all providers
    vegetation: list[VegetationObservation] = Field(
        default_factory=list, description="Vegetation indices"
    )

    # Overall quality metrics
    overall_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Aggregate quality score"
    )
    providers_attempted: list[str] = Field(
        default_factory=list, description="All providers attempted"
    )
    providers_successful: list[str] = Field(
        default_factory=list, description="Providers that returned data"
    )

    # Error tracking
    errors: list[str] = Field(
        default_factory=list, description="Error messages from failed providers"
    )
    warnings: list[str] = Field(default_factory=list, description="Warning messages")

    @field_validator("requested_location")
    @classmethod
    def validate_requested_location(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate requested location coordinates."""
        if "lat" not in v or "lon" not in v:
            raise ValueError("Requested location must contain 'lat' and 'lon' keys")

        lat, lon = v["lat"], v["lon"]
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

        return v

    def to_nmdc_schema(self) -> dict[str, Any]:
        """Convert to NMDC schema format."""
        nmdc_data: dict[str, Any] = {}

        # Add current vegetation field if we have land cover data
        if self.land_cover:
            # Use highest confidence land cover classification
            best_lc = max(self.land_cover, key=lambda x: x.confidence or 0.0)

            if best_lc.class_label:
                nmdc_data["cur_vegetation"] = {
                    "has_raw_value": best_lc.class_label,
                    "type": "nmdc:TextValue",
                }

        # Add vegetation indices
        if self.vegetation:
            # Use temporally closest vegetation data
            best_veg = min(
                [v for v in self.vegetation if v.temporal_offset_days is not None],
                key=lambda x: abs(x.temporal_offset_days),
                default=self.vegetation[0] if self.vegetation else None,
            )

            if best_veg:
                if best_veg.ndvi is not None:
                    nmdc_data["ndvi"] = {
                        "has_numeric_value": best_veg.ndvi,
                        "has_unit": "1",
                        "type": "nmdc:QuantityValue",
                    }

                if best_veg.evi is not None:
                    nmdc_data["evi"] = {
                        "has_numeric_value": best_veg.evi,
                        "has_unit": "1",
                        "type": "nmdc:QuantityValue",
                    }

                if best_veg.lai is not None:
                    nmdc_data["lai"] = {
                        "has_numeric_value": best_veg.lai,
                        "has_unit": "m^2/m^2",
                        "type": "nmdc:QuantityValue",
                    }

        return nmdc_data

    def to_gold_schema(self) -> dict[str, Any]:
        """Convert to GOLD schema format."""
        gold_data: dict[str, Any] = {}

        # Combine land cover and vegetation information
        habitat_details = []
        env_params = {}

        # Add land cover information
        if self.land_cover:
            for lc in self.land_cover:
                if lc.class_label:
                    detail = f"Land cover: {lc.class_label}"
                    if lc.provider:
                        detail += f" ({lc.provider})"
                    habitat_details.append(detail)

        # Add vegetation indices to environmental parameters
        if self.vegetation:
            for veg in self.vegetation:
                provider_prefix = veg.provider.lower().replace(" ", "_")

                if veg.ndvi is not None:
                    env_params[f"{provider_prefix}_ndvi"] = veg.ndvi
                if veg.evi is not None:
                    env_params[f"{provider_prefix}_evi"] = veg.evi
                if veg.lai is not None:
                    env_params[f"{provider_prefix}_lai"] = veg.lai
                if veg.fpar is not None:
                    env_params[f"{provider_prefix}_fpar"] = veg.fpar

        if habitat_details:
            gold_data["habitatDetails"] = "; ".join(habitat_details)

        if env_params:
            gold_data["environmentalParameters"] = env_params

        return gold_data
