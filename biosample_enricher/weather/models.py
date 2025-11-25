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


class MultiProviderClimateNormals(BaseModel):
    """
    Climate normals from multiple providers for comparison and validation.

    Returns results from all requested providers, allowing users to:
    - Compare values across different data sources
    - Detect provider outages/failures
    - Validate data quality by cross-checking
    - Choose which provider to trust for their use case

    This is the default return type when multiple providers are queried.
    """

    # Results from each provider (keyed by provider name)
    providers: dict[
        str, "ClimateNormalsResult"
    ]  # e.g., {"meteostat": <result>, "nasa_power": <result>}

    # Summary statistics across providers
    location: dict[str, float]  # {"lat": 42.5, "lon": -85.4}
    requested_providers: list[str]  # Providers that were attempted
    successful_providers: list[str]  # Providers that returned data
    failed_providers: dict[str, str]  # Provider name -> error message
    requested_start_year: int  # Requested start year (computed from years_back)
    requested_end_year: int  # Requested end year (current year)

    def get_provider_result(self, provider_name: str) -> "ClimateNormalsResult | None":
        """Get result from a specific provider."""
        return self.providers.get(provider_name)

    def get_consensus_precipitation(self) -> float | None:
        """
        Calculate consensus annual precipitation across all successful providers.

        Returns the mean precipitation if multiple providers available,
        otherwise returns the single provider's value.
        """
        precip_values = []
        for result in self.providers.values():
            value = result.get_annual_precipitation()
            if value is not None:
                precip_values.append(value)

        if not precip_values:
            return None

        return sum(precip_values) / len(precip_values)

    def get_consensus_temperature(self) -> float | None:
        """
        Calculate consensus annual temperature across all successful providers.

        Returns the mean temperature if multiple providers available,
        otherwise returns the single provider's value.
        """
        temp_values = []
        for result in self.providers.values():
            value = result.get_annual_temperature()
            if value is not None:
                temp_values.append(value)

        if not temp_values:
            return None

        return sum(temp_values) / len(temp_values)

    def get_value_ranges(self) -> dict[str, tuple[float, float] | None]:
        """
        Get min/max range of values across providers.

        Useful for detecting large discrepancies and data quality issues.

        Returns:
            Dict with keys:
            - annual_precpt_range: (min, max) in mm/year or None
            - annual_temp_range: (min, max) in °C or None
        """
        precip_values: list[float] = [
            p
            for result in self.providers.values()
            if (p := result.get_annual_precipitation()) is not None
        ]
        temp_values: list[float] = [
            t
            for result in self.providers.values()
            if (t := result.get_annual_temperature()) is not None
        ]

        return {
            "annual_precpt_range": (min(precip_values), max(precip_values))
            if precip_values
            else None,
            "annual_temp_range": (min(temp_values), max(temp_values))
            if temp_values
            else None,
        }

    def to_submission_schema(
        self, provider: str | None = None, strategy: str = "mean"
    ) -> dict[str, Any]:
        """
        Extract values in submission-schema compatible format.

        Args:
            provider: Specific provider to use (e.g., "meteostat"). If None, uses strategy.
            strategy: How to combine multiple providers:
                     - "mean": Average across all successful providers (default)
                     - "median": Middle value when sorted (robust to outliers)
                     - "first": Use first successful provider
                     - "best_quality": Use provider with lowest station_distance_km

        Returns:
            Dict with submission-schema values plus metadata about provider selection
        """
        if provider:
            # Use specific provider
            result = self.providers.get(provider)
            if not result:
                raise ValueError(f"Provider {provider} not available in results")
            return result.to_submission_schema()

        if strategy == "mean":
            return {
                "annual_precpt": self.get_consensus_precipitation(),
                "annual_temp": self.get_consensus_temperature(),
                "data_strategy": "mean",
                "providers_used": self.successful_providers,
            }
        elif strategy == "median":
            # Calculate median across providers
            precip_values: list[float] = [
                p
                for r in self.providers.values()
                if (p := r.get_annual_precipitation()) is not None
            ]
            temp_values: list[float] = [
                t
                for r in self.providers.values()
                if (t := r.get_annual_temperature()) is not None
            ]
            return {
                "annual_precpt": sorted(precip_values)[len(precip_values) // 2]
                if precip_values
                else None,
                "annual_temp": sorted(temp_values)[len(temp_values) // 2]
                if temp_values
                else None,
                "data_strategy": "median",
                "providers_used": self.successful_providers,
            }
        elif strategy == "first":
            # Use first successful provider
            first_provider = (
                self.successful_providers[0] if self.successful_providers else None
            )
            if not first_provider:
                return {
                    "annual_precpt": None,
                    "annual_temp": None,
                    "error": "No successful providers",
                }
            return self.providers[first_provider].to_submission_schema()
        elif strategy == "best_quality":
            # Use provider with lowest station distance (for station-based providers)
            best_provider = min(
                self.providers.items(),
                key=lambda x: x[1].station_distance_km
                if x[1].station_distance_km
                else float("inf"),
            )
            return best_provider[1].to_submission_schema()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")


class ClimateNormalsResult(BaseModel):
    """
    30-year climate averages (normals) from a single provider.

    Climate normals provide baseline environmental conditions over a standard
    30-year period (typically 1991-2020), representing typical climate rather
    than day-to-day weather variability.

    Use this for:
    - Annual precipitation totals (sum of 12 monthly means)
    - Annual temperature averages
    - Long-term climate characterization
    - Biosample metadata fields like annual_precpt, annual_temp

    For day-specific weather conditions, use WeatherResult instead.
    For multi-provider comparisons, see MultiProviderClimateNormals.
    """

    # Monthly climate normals (mm for precipitation, °C for temperature)
    monthly_precipitation: list[float | None]  # 12 values, one per month (mm)
    monthly_temperature: list[float | None]  # 12 values, one per month (°C)

    # Station metadata
    station_id: str
    station_distance_km: float  # Distance from requested location
    location: dict[str, float]  # {"lat": 42.5, "lon": -85.4}
    normals_period: tuple[int, int]  # (start_year, end_year), e.g., (1991, 2020)

    # Provider info
    provider: str = "meteostat"
    data_quality: str | None = None  # Quality assessment notes

    def get_annual_precipitation(self) -> float | None:
        """
        Calculate annual precipitation by summing 12 monthly normals.

        Returns total in millimeters, suitable for submission-schema
        annual_precpt slot.

        Returns:
            float: Annual precipitation in millimeters (mm/year), or None if
                data incomplete (requires at least 10 months of valid data).

        Example:
            >>> result.get_annual_precipitation()
            547.2  # mm/year
        """
        if not self.monthly_precipitation:
            return None

        # Filter out None values and sum
        valid_months = [p for p in self.monthly_precipitation if p is not None]

        # Require at least 10 months of data for reasonable estimate
        if len(valid_months) < 10:
            return None

        return sum(valid_months)

    def get_annual_temperature(self) -> float | None:
        """
        Calculate annual average temperature from 12 monthly normals.

        Returns average in degrees Celsius, suitable for submission-schema
        annual_temp slot.

        Returns:
            Annual average temperature in °C, or None if data incomplete.

        Example:
            >>> result.get_annual_temperature()
            12.5  # °C
        """
        if not self.monthly_temperature:
            return None

        # Filter out None values and average
        valid_months = [t for t in self.monthly_temperature if t is not None]

        # Require at least 10 months of data for reasonable estimate
        if len(valid_months) < 10:
            return None

        return sum(valid_months) / len(valid_months)

    def to_submission_schema(self) -> dict[str, Any]:
        """
        Extract values in submission-schema compatible format.

        Provides simple scalar values suitable for NMDC submission-schema
        slots, following general-purpose design pattern (Issue #193).

        Returns:
            Dict with keys:
            - annual_precpt: float | None - Annual precipitation in millimeters
              (mm/year). Sum of 12 monthly normals. None if <10 months available.
            - annual_temp: float | None - Annual average temperature in degrees
              Celsius (°C). Average of 12 monthly normals. None if <10 months.
            - climate_normals_period: str - Period as "YYYY-YYYY" (e.g. "1991-2020")
            - station_distance_km: float - Distance to weather station in kilometers
            - data_source: str - Provider name (e.g. "meteostat")

        Example:
            >>> normals = service.get_climate_normals(37.7749, -122.4194)
            >>> values = normals.to_submission_schema()
            >>> print(f"Annual rainfall: {values['annual_precpt']} mm")
            Annual rainfall: 547.2 mm
        """
        return {
            "annual_precpt": self.get_annual_precipitation(),
            "annual_temp": self.get_annual_temperature(),
            "climate_normals_period": f"{self.normals_period[0]}-{self.normals_period[1]}",
            "station_distance_km": self.station_distance_km,
            "data_source": self.provider,
        }
