"""
Open-Meteo weather provider for comprehensive historical and forecast weather data.

Open-Meteo API provides:
- Historical data: 1959-present
- No API key required
- Hourly resolution
- Global coverage
- High-quality reanalysis data
"""

from datetime import date
from typing import Any

import pandas as pd

from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.weather.models import (
    TemporalPrecision,
    TemporalQuality,
    WeatherObservation,
    WeatherResult,
)
from biosample_enricher.weather.providers.base import WeatherProviderBase

logger = get_logger(__name__)


class OpenMeteoProvider(WeatherProviderBase):
    """
    Open-Meteo weather data provider for biosample enrichment.

    Provides day-specific weather data by aggregating hourly observations
    with proper temporal precision tracking and quality assessment.
    """

    BASE_URL = "https://archive-api.open-meteo.com/v1/era5"

    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
        self.provider_name = "open_meteo"

    def get_daily_weather(
        self,
        lat: float,
        lon: float,
        target_date: date,
        parameters: list[str] | None = None,
    ) -> WeatherResult:
        """
        Get daily weather data for specific date and location from Open-Meteo.

        Fetches hourly data and aggregates to daily statistics with temporal
        precision tracking for biosample enrichment workflows.
        """
        logger.info(f"Fetching Open-Meteo weather for ({lat}, {lon}) on {target_date}")

        # Default to all core parameters if none specified
        if parameters is None:
            parameters = [
                "temperature_2m",
                "precipitation",
                "wind_speed_10m",
                "wind_direction_10m",
                "relative_humidity_2m",
                "surface_pressure",
                "shortwave_radiation",
            ]

        try:
            # Fetch hourly data for target date
            hourly_data = self._fetch_hourly_data(lat, lon, target_date, parameters)

            if hourly_data.empty:
                return self._create_empty_result(
                    lat, lon, target_date, "No hourly data available"
                )

            # Aggregate hourly to daily with coverage assessment
            daily_aggregates = self._aggregate_hourly_to_daily(hourly_data, target_date)

            # Convert to standardized WeatherResult
            weather_result = self._convert_to_weather_result(
                daily_aggregates, lat, lon, target_date
            )

            logger.info(
                f"Successfully retrieved Open-Meteo weather with {len(weather_result.successful_providers)} parameters"
            )
            return weather_result

        except Exception as e:
            logger.error(f"Open-Meteo provider failed: {e}")
            return self._create_empty_result(
                lat, lon, target_date, f"Provider error: {e}"
            )

    def _fetch_hourly_data(
        self, lat: float, lon: float, target_date: date, parameters: list[str]
    ) -> pd.DataFrame:
        """Fetch hourly weather data from Open-Meteo API."""

        # Format date for API request
        date_str = target_date.strftime("%Y-%m-%d")

        # Build API request
        api_params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": ",".join(parameters),
            "timezone": "UTC",
        }

        logger.debug(
            f"Open-Meteo API request: {self.BASE_URL} with params: {api_params}"
        )

        response = request(
            method="GET",
            url=self.BASE_URL,
            params=api_params,
            timeout=self.timeout,
            read_from_cache=True,
            write_to_cache=True,
        )

        if response.status_code != 200:
            logger.error(f"Open-Meteo API request failed: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            logger.error(f"Request URL: {response.url}")
            raise Exception(f"Open-Meteo API error: {response.status_code}")

        data = response.json()

        # Convert to DataFrame
        if "hourly" not in data:
            return pd.DataFrame()

        hourly = data["hourly"]
        df = pd.DataFrame(hourly)

        # Parse datetime
        if "time" in df.columns:
            df["datetime"] = pd.to_datetime(df["time"])
            df = df.set_index("datetime")

        return df

    def _aggregate_hourly_to_daily(
        self, hourly_df: pd.DataFrame, _target_date: date
    ) -> dict[str, Any]:
        """
        Aggregate hourly weather data to daily statistics.

        Args:
            hourly_df: DataFrame with hourly weather observations
            target_date: Target date for aggregation

        Returns:
            Dict with daily aggregates and coverage metadata
        """
        if hourly_df.empty:
            return {"coverage": "none", "method": "no_data", "aggregates": {}}

        total_hours = 24
        available_hours = len(hourly_df.dropna(how="all"))
        coverage_fraction = available_hours / total_hours

        aggregates = {}

        # Temperature aggregation (min/max/avg)
        if "temperature_2m" in hourly_df.columns:
            temp_data = hourly_df["temperature_2m"].dropna()
            if len(temp_data) > 0:
                aggregates["temperature"] = {
                    "min": float(temp_data.min()),
                    "max": float(temp_data.max()),
                    "avg": float(temp_data.mean()),
                    "unit": "Celsius",
                }

        # Precipitation (sum)
        if "precipitation" in hourly_df.columns:
            precip_data = hourly_df["precipitation"].dropna()
            if len(precip_data) > 0:
                aggregates["precipitation"] = {
                    "sum": float(precip_data.sum()),
                    "unit": "mm",
                }

        # Wind speed (min/max/avg)
        if "wind_speed_10m" in hourly_df.columns:
            wind_speed_data = hourly_df["wind_speed_10m"].dropna()
            if len(wind_speed_data) > 0:
                aggregates["wind_speed"] = {
                    "min": float(wind_speed_data.min()),
                    "max": float(wind_speed_data.max()),
                    "avg": float(wind_speed_data.mean()),
                    "unit": "m/s",
                }

        # Wind direction (vector mean)
        if "wind_direction_10m" in hourly_df.columns:
            wind_dir_data = hourly_df["wind_direction_10m"].dropna()
            if len(wind_dir_data) > 0:
                # Calculate vector mean for wind direction
                import math

                sin_sum = sum(math.sin(math.radians(d)) for d in wind_dir_data)
                cos_sum = sum(math.cos(math.radians(d)) for d in wind_dir_data)
                vector_mean = math.degrees(math.atan2(sin_sum, cos_sum)) % 360

                aggregates["wind_direction"] = {
                    "vector_mean": float(vector_mean),
                    "unit": "degrees",
                }

        # Humidity (avg)
        if "relative_humidity_2m" in hourly_df.columns:
            humidity_data = hourly_df["relative_humidity_2m"].dropna()
            if len(humidity_data) > 0:
                aggregates["humidity"] = {
                    "avg": float(humidity_data.mean()),
                    "unit": "percent",
                }

        # Pressure (avg)
        if "surface_pressure" in hourly_df.columns:
            pressure_data = hourly_df["surface_pressure"].dropna()
            if len(pressure_data) > 0:
                aggregates["pressure"] = {
                    "avg": float(pressure_data.mean() / 1000),  # Pa to kPa
                    "unit": "kPa",
                }

        # Solar radiation (sum, convert J/m² to W/m²)
        if "shortwave_radiation" in hourly_df.columns:
            solar_data = hourly_df["shortwave_radiation"].dropna()
            if len(solar_data) > 0:
                # Convert from J/m² per hour to W/m² daily average
                daily_avg_wm2 = float(solar_data.mean() / 3600)  # J/h to W
                aggregates["solar_radiation"] = {
                    "daily_avg": daily_avg_wm2,
                    "unit": "W/m2",
                }

        return {
            "coverage": "complete" if coverage_fraction >= 0.8 else "partial",
            "coverage_fraction": coverage_fraction,
            "available_hours": available_hours,
            "total_hours": total_hours,
            "method": "hourly_aggregation",
            "aggregates": aggregates,
        }

    def _convert_to_weather_result(
        self,
        daily_aggregates: dict[str, Any],
        lat: float,
        lon: float,
        target_date: date,
    ) -> WeatherResult:
        """Convert Open-Meteo daily aggregates to standardized WeatherResult."""

        if not daily_aggregates.get("aggregates"):
            return self._create_empty_result(
                lat, lon, target_date, "No weather data aggregated"
            )

        aggregates = daily_aggregates["aggregates"]
        coverage = daily_aggregates.get("coverage", "none")

        # Determine temporal quality
        temporal_quality = (
            TemporalQuality.DAY_SPECIFIC_COMPLETE
            if coverage == "complete"
            else TemporalQuality.DAY_SPECIFIC_PARTIAL
            if coverage == "partial"
            else TemporalQuality.NO_DATA
        )

        # Create temporal precision metadata
        temporal_precision = TemporalPrecision(
            method="hourly_aggregation",
            target_date=target_date.strftime("%Y-%m-%d"),
            data_quality=temporal_quality,
            coverage_info=f"{daily_aggregates.get('available_hours', 0)}/24 hours",
            provider="open_meteo",
        )

        # Convert aggregates to WeatherObservation objects
        observations = {}

        if "temperature" in aggregates:
            temp_data = aggregates["temperature"]
            # Extract numerical values only (exclude 'unit' key)
            temp_values = {k: v for k, v in temp_data.items() if k != "unit"}
            observations["temperature"] = WeatherObservation(
                value=temp_values,  # Contains min/max/avg only
                unit=temp_data["unit"],
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(temporal_quality, 1.0),
            )

        if "wind_speed" in aggregates:
            wind_data = aggregates["wind_speed"]
            # Extract numerical values only (exclude 'unit' key)
            wind_values = {k: v for k, v in wind_data.items() if k != "unit"}
            observations["wind_speed"] = WeatherObservation(
                value=wind_values,  # Contains min/max/avg only
                unit=wind_data["unit"],
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(temporal_quality, 1.0),
            )

        if "wind_direction" in aggregates:
            wind_dir_data = aggregates["wind_direction"]
            observations["wind_direction"] = WeatherObservation(
                value=wind_dir_data["vector_mean"],
                unit=wind_dir_data["unit"],
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(temporal_quality, 1.0),
            )

        if "humidity" in aggregates:
            humidity_data = aggregates["humidity"]
            observations["humidity"] = WeatherObservation(
                value=humidity_data["avg"],
                unit=humidity_data["unit"],
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(temporal_quality, 1.0),
            )

        if "solar_radiation" in aggregates:
            solar_data = aggregates["solar_radiation"]
            observations["solar_radiation"] = WeatherObservation(
                value=solar_data["daily_avg"],
                unit=solar_data["unit"],
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(temporal_quality, 1.0),
            )

        if "precipitation" in aggregates:
            precip_data = aggregates["precipitation"]
            observations["precipitation"] = WeatherObservation(
                value=precip_data["sum"],
                unit=precip_data["unit"],
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(temporal_quality, 1.0),
            )

        if "pressure" in aggregates:
            pressure_data = aggregates["pressure"]
            observations["pressure"] = WeatherObservation(
                value=pressure_data["avg"],
                unit=pressure_data["unit"],
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(temporal_quality, 1.0),
            )

        return WeatherResult(
            location={"lat": lat, "lon": lon},
            collection_date=target_date.strftime("%Y-%m-%d"),
            providers_attempted=["open_meteo"],
            successful_providers=["open_meteo"],
            failed_providers=[],
            overall_quality=temporal_quality,
            **observations,
        )

    def _create_empty_result(
        self, lat: float, lon: float, target_date: date, _error_msg: str
    ) -> WeatherResult:
        """Create empty WeatherResult for failed requests."""
        return WeatherResult(
            location={"lat": lat, "lon": lon},
            collection_date=target_date.strftime("%Y-%m-%d"),
            providers_attempted=["open_meteo"],
            successful_providers=[],
            failed_providers=["open_meteo"],
            overall_quality=TemporalQuality.NO_DATA,
        )

    def is_available(self, _lat: float, _lon: float, target_date: date) -> bool:
        """Check if Open-Meteo has data for the given location and date."""
        # Open-Meteo ERA5 data available globally from 1959-present
        start_date = date(1959, 1, 1)
        end_date = date.today()

        return start_date <= target_date <= end_date

    def get_supported_parameters(self) -> list[str]:
        """Return list of weather parameters supported by Open-Meteo."""
        return [
            "temperature_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "relative_humidity_2m",
            "surface_pressure",
            "shortwave_radiation",
        ]

    def get_temporal_resolution(self) -> str:
        """Return temporal resolution."""
        return "hourly"

    def get_spatial_resolution(self) -> str:
        """Return spatial resolution."""
        return "11km"  # ERA5 native resolution

    def get_coverage_period(self) -> dict[str, str]:
        """Return temporal coverage period."""
        return {
            "start": "1959-01-01",
            "end": "present",
            "description": "ERA5 reanalysis global coverage",
        }
