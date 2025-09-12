"""
Marine enrichment data models with standardized schema for oceanographic metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MarineQuality(str, Enum):
    """Data quality levels for marine observations."""

    SATELLITE_L3 = "satellite_l3"  # Level 3 satellite product (daily composite)
    SATELLITE_L4 = "satellite_l4"  # Level 4 satellite product (gap-filled)
    MODEL_REANALYSIS = "model_reanalysis"  # Ocean model reanalysis
    CLIMATOLOGY = "climatology"  # Long-term climatological average
    STATIC_DATASET = "static_dataset"  # Static bathymetry/geographic data
    NO_DATA = "no_data"  # No marine data available


class MarineProvider(str, Enum):
    """Supported marine data providers."""

    NOAA_OISST = "noaa_oisst"  # NOAA Optimum Interpolation SST
    GEBCO = "gebco"  # General Bathymetric Chart of the Oceans
    ESA_CCI = "esa_cci"  # ESA Climate Change Initiative Ocean Colour
    CMEMS = "cmems"  # Copernicus Marine Environment Monitoring Service
    OSCAR = "oscar"  # Ocean Surface Current Analyses Real-time


@dataclass
class MarinePrecision:
    """Precision metadata for marine observations."""

    method: str  # "satellite_composite", "bathymetric_grid", etc.
    target_date: str  # "2018-07-12" - collection date target
    data_quality: MarineQuality  # Quality assessment
    spatial_resolution: str | None = None  # "0.25°", "15 arc-seconds", etc.
    temporal_resolution: str | None = None  # "daily", "static", etc.
    provider: str | None = None  # Data source


class MarineObservation(BaseModel):
    """Single marine parameter observation with units and precision context."""

    value: float | dict[str, float]  # Scalar value or {min, max, avg}
    unit: str  # Standard oceanographic units
    precision: MarinePrecision  # Precision metadata
    quality_score: int | None = Field(None, ge=0, le=100)  # 0-100 quality score
    uncertainty: float | None = None  # Measurement uncertainty

    @field_validator("value")
    @classmethod
    def validate_value(cls, v):
        """Validate observation value."""
        if isinstance(v, dict):
            required_keys = {"min", "max", "avg"}
            if not required_keys.issubset(v.keys()):
                raise ValueError(f"Dictionary value must contain keys: {required_keys}")
            if not all(isinstance(val, int | float) for val in v.values()):
                raise ValueError("All dictionary values must be numeric")
        elif not isinstance(v, int | float):
            raise ValueError("Value must be numeric or dictionary")
        return v


class MarineResult(BaseModel):
    """Complete marine data result for a location and date."""

    location: dict[str, float]  # {"lat": 42.5, "lon": -85.4}
    collection_date: str  # "2018-07-12"

    # Core marine parameters (Tier 1 priority)
    sea_surface_temperature: MarineObservation | None = None
    bathymetry: MarineObservation | None = (
        None  # Water depth (negative for below sea level)
    )
    chlorophyll_a: MarineObservation | None = None

    # Extended marine parameters (Tier 2)
    salinity: MarineObservation | None = None
    dissolved_oxygen: MarineObservation | None = None
    ph: MarineObservation | None = None
    ocean_current_u: MarineObservation | None = None  # Eastward velocity
    ocean_current_v: MarineObservation | None = None  # Northward velocity
    significant_wave_height: MarineObservation | None = None

    # Provider tracking
    successful_providers: list[str] = Field(default_factory=list)
    failed_providers: list[str] = Field(default_factory=list)
    overall_quality: MarineQuality = MarineQuality.NO_DATA

    @field_validator("collection_date")
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError("collection_date must be in YYYY-MM-DD format") from e

    def get_schema_mapping(self, target_schema: str) -> dict[str, Any]:
        """Map marine data to target biosample schema.

        Args:
            target_schema: "nmdc" or "gold"

        Returns:
            Dictionary mapping to schema fields
        """
        mapping: dict[str, Any] = {}

        if target_schema.lower() == "nmdc":
            # NMDC schema mappings
            if self.sea_surface_temperature:
                mapping["temp"] = {
                    "has_numeric_value": self._extract_value(
                        self.sea_surface_temperature
                    ),
                    "has_unit": self.sea_surface_temperature.unit,
                    "type": "nmdc:QuantityValue",
                }

            if self.bathymetry:
                mapping["tot_depth_water_col"] = {
                    "has_numeric_value": abs(
                        self._extract_value(self.bathymetry)
                    ),  # Positive depth
                    "has_unit": self.bathymetry.unit,
                    "type": "nmdc:QuantityValue",
                }
                mapping["elev"] = {
                    "has_numeric_value": self._extract_value(
                        self.bathymetry
                    ),  # Negative elevation
                    "has_unit": self.bathymetry.unit,
                    "type": "nmdc:QuantityValue",
                }

            if self.chlorophyll_a:
                mapping["chlorophyll"] = {
                    "has_numeric_value": self._extract_value(self.chlorophyll_a),
                    "has_unit": self.chlorophyll_a.unit,
                    "type": "nmdc:QuantityValue",
                }

            if self.salinity:
                mapping["salinity"] = {
                    "has_numeric_value": self._extract_value(self.salinity),
                    "has_unit": self.salinity.unit,
                    "type": "nmdc:QuantityValue",
                }

            if self.dissolved_oxygen:
                mapping["diss_oxygen"] = {
                    "has_numeric_value": self._extract_value(self.dissolved_oxygen),
                    "has_unit": self.dissolved_oxygen.unit,
                    "type": "nmdc:QuantityValue",
                }

            if self.ph:
                mapping["ph"] = {
                    "has_numeric_value": self._extract_value(self.ph),
                    "has_unit": self.ph.unit,
                    "type": "nmdc:QuantityValue",
                }

        elif target_schema.lower() == "gold":
            # GOLD schema mappings
            if self.sea_surface_temperature:
                mapping["sampleCollectionTemperature"] = (
                    f"{self._extract_value(self.sea_surface_temperature)} {self.sea_surface_temperature.unit}"
                )

            if self.bathymetry:
                mapping["depthInMeters"] = abs(
                    self._extract_value(self.bathymetry)
                )  # Positive depth
                mapping["elevationInMeters"] = self._extract_value(
                    self.bathymetry
                )  # Negative elevation

            if self.salinity:
                mapping["salinity"] = (
                    f"{self._extract_value(self.salinity)} {self.salinity.unit}"
                )
                mapping["salinityConcentration"] = (
                    f"{self._extract_value(self.salinity)} {self.salinity.unit}"
                )

            if self.dissolved_oxygen:
                mapping["oxygenConcentration"] = (
                    f"{self._extract_value(self.dissolved_oxygen)} {self.dissolved_oxygen.unit}"
                )

            if self.ph:
                mapping["ph"] = self._extract_value(self.ph)

        return mapping

    def _extract_value(self, observation: MarineObservation) -> float:
        """Extract single value from observation (avg if dict)."""
        if isinstance(observation.value, dict):
            return observation.value.get("avg", observation.value.get("mean", 0.0))
        return observation.value

    def get_coverage_metrics(self) -> dict[str, Any]:
        """Generate coverage metrics for this marine result."""
        marine_fields = [
            "sea_surface_temperature",
            "bathymetry",
            "chlorophyll_a",
            "salinity",
            "dissolved_oxygen",
            "ph",
            "ocean_current_u",
            "ocean_current_v",
            "significant_wave_height",
        ]

        enriched_fields = []
        quality_scores = []

        for field in marine_fields:
            observation = getattr(self, field)
            if observation is not None:
                enriched_fields.append(field)
                if observation.quality_score is not None:
                    quality_scores.append(observation.quality_score)

        return {
            "enriched_count": len(enriched_fields),
            "total_possible_fields": len(marine_fields),
            "enrichment_percentage": (len(enriched_fields) / len(marine_fields)) * 100,
            "enriched_fields": enriched_fields,
            "average_quality_score": sum(quality_scores) / len(quality_scores)
            if quality_scores
            else None,
            "data_quality": self.overall_quality.value,
            "successful_providers": self.successful_providers,
            "provider_count": len(self.successful_providers),
        }
