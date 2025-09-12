"""
Weather enrichment data models with standardized schema for biosample metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class TemporalQuality(str, Enum):
    """Temporal precision quality levels for weather data."""

    DAY_SPECIFIC_COMPLETE = "day_specific_complete"  # 24h coverage on exact date
    DAY_SPECIFIC_PARTIAL = "day_specific_partial"  # >12h coverage on exact date
    WEEKLY_COMPOSITE = "weekly_composite"  # 7-day average centered on date
    MONTHLY_CLIMATOLOGY = "monthly_climatology"  # Long-term monthly average
    NO_DATA = "no_data"  # No weather data available


class WeatherProvider(str, Enum):
    """Supported weather data providers."""

    OPEN_METEO = "open_meteo"
    METEOSTAT = "meteostat"
    NOAA = "noaa"
    ECMWF = "ecmwf"


@dataclass
class TemporalPrecision:
    """Temporal precision metadata for weather observations."""

    method: str  # "hourly_aggregation", "daily_composite", etc.
    target_date: str  # "2018-07-12" - collection date target
    data_quality: TemporalQuality  # Quality assessment
    coverage_info: str | None = None  # "20/24 hours", "7-day window", etc.
    caveat: str | None = None  # Data quality warnings
    provider: str | None = None  # Data source


class WeatherObservation(BaseModel):
    """Single weather parameter observation with units and temporal context."""

    value: float | dict[str, float]  # Scalar value or {min, max, avg}
    unit: str  # SI units preferred
    temporal_precision: TemporalPrecision  # Temporal metadata
    quality_score: int | None = Field(None, ge=0, le=100)  # 0-100 quality score

    class Config:
        arbitrary_types_allowed = True

    @validator("value")
    def validate_value(cls, v):
        """Validate that value is either a number or dict with numeric values."""
        if isinstance(v, dict):
            # Allow dict with numeric values but exclude 'unit' key
            numeric_dict = {
                k: val
                for k, val in v.items()
                if k != "unit" and isinstance(val, int | float)
            }
            return numeric_dict
        return v


class WeatherResult(BaseModel):
    """
    Standardized weather enrichment result aligned with NMDC/GOLD schemas.

    Maps weather API responses to biosample schema fields with temporal precision.
    """

    # Core atmospheric parameters
    temperature: WeatherObservation | None = (
        None  # → temp, avg_temp, sampleCollectionTemperature
    )
    wind_speed: WeatherObservation | None = None  # → wind_speed
    wind_direction: WeatherObservation | None = None  # → wind_direction
    humidity: WeatherObservation | None = None  # → humidity
    solar_radiation: WeatherObservation | None = None  # → solar_irradiance
    precipitation: WeatherObservation | None = None  # → New field
    pressure: WeatherObservation | None = None  # → pressure (GOLD)

    # Enrichment metadata
    location: dict[str, float]  # {"lat": 42.5, "lon": -85.4}
    collection_date: str  # "2018-07-12"
    providers_attempted: list[str] = Field(default_factory=list)
    successful_providers: list[str] = Field(default_factory=list)
    failed_providers: list[str] = Field(default_factory=list)
    overall_quality: TemporalQuality | None = None

    @validator("collection_date")
    def validate_date_format(cls, v):
        """Ensure collection date is in YYYY-MM-DD format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError("collection_date must be in YYYY-MM-DD format") from e

    def get_schema_mapping(self, target_schema: str = "nmdc") -> dict[str, Any]:
        """
        Map weather observations to target biosample schema fields.

        Args:
            target_schema: "nmdc" or "gold"

        Returns:
            Dict mapping to schema field names and values
        """
        if target_schema.lower() == "nmdc":
            return self._get_nmdc_mapping()
        elif target_schema.lower() == "gold":
            return self._get_gold_mapping()
        else:
            raise ValueError(f"Unsupported schema: {target_schema}")

    def _get_nmdc_mapping(self) -> dict[str, Any]:
        """Map to NMDC biosample schema fields."""
        mapping = {}

        if self.temperature:
            # Handle both scalar and aggregated temperature
            if isinstance(self.temperature.value, dict):
                # Daily aggregation: min/max/avg
                mapping["temp"] = {
                    "has_numeric_value": self.temperature.value.get("avg"),
                    "has_unit": self.temperature.unit,
                    "type": "nmdc:QuantityValue",
                    "temp_min": self.temperature.value.get("min"),
                    "temp_max": self.temperature.value.get("max"),
                }
            else:
                # Single value
                mapping["temp"] = {
                    "has_numeric_value": self.temperature.value,
                    "has_unit": self.temperature.unit,
                    "type": "nmdc:QuantityValue",
                }

        if self.wind_speed:
            mapping["wind_speed"] = {
                "has_numeric_value": self.wind_speed.value
                if isinstance(self.wind_speed.value, int | float)
                else self.wind_speed.value.get("avg"),
                "has_unit": self.wind_speed.unit,
                "type": "nmdc:QuantityValue",
            }

        if self.wind_direction:
            mapping["wind_direction"] = {
                "has_raw_value": str(self.wind_direction.value),
                "type": "nmdc:TextValue",
            }

        if self.humidity:
            mapping["humidity"] = {
                "has_numeric_value": self.humidity.value
                if isinstance(self.humidity.value, int | float)
                else self.humidity.value.get("avg"),
                "has_unit": self.humidity.unit,
                "type": "nmdc:QuantityValue",
            }

        if self.solar_radiation:
            mapping["solar_irradiance"] = {
                "has_numeric_value": self.solar_radiation.value
                if isinstance(self.solar_radiation.value, int | float)
                else self.solar_radiation.value.get("daily_avg"),
                "has_unit": self.solar_radiation.unit,
                "type": "nmdc:QuantityValue",
            }

        return mapping

    def _get_gold_mapping(self) -> dict[str, Any]:
        """Map to GOLD biosample schema fields."""
        mapping = {}

        if self.temperature:
            temp_value = (
                self.temperature.value
                if isinstance(self.temperature.value, int | float)
                else self.temperature.value.get("avg")
            )
            mapping["sampleCollectionTemperature"] = (
                f"{temp_value} {self.temperature.unit}"
            )

        if self.pressure:
            mapping["pressure"] = f"{self.pressure.value} {self.pressure.unit}"

        return mapping

    def get_coverage_metrics(self) -> dict[str, Any]:
        """
        Generate before/after coverage metrics for this weather enrichment.

        Returns:
            Dict with coverage statistics for metrics reporting
        """
        enriched_fields = []
        quality_scores = []

        for field_name, observation in [
            ("temperature", self.temperature),
            ("wind_speed", self.wind_speed),
            ("wind_direction", self.wind_direction),
            ("humidity", self.humidity),
            ("solar_radiation", self.solar_radiation),
            ("precipitation", self.precipitation),
            ("pressure", self.pressure),
        ]:
            if observation is not None:
                enriched_fields.append(field_name)
                if observation.quality_score:
                    quality_scores.append(observation.quality_score)

        return {
            "enriched_fields": enriched_fields,
            "enriched_count": len(enriched_fields),
            "total_possible_fields": 7,
            "enrichment_percentage": (len(enriched_fields) / 7) * 100,
            "average_quality_score": sum(quality_scores) / len(quality_scores)
            if quality_scores
            else 0,
            "temporal_quality": self.overall_quality.value
            if self.overall_quality
            else "no_data",
            "successful_providers": self.successful_providers,
            "provider_count": len(self.successful_providers),
        }
