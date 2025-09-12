"""
MeteoStat weather provider for station-based historical weather data.

MeteoStat provides:
- Historical weather station data: 1973-present
- High-quality ground-based observations
- Global coverage with 120,000+ stations
- No API key required (uses Python library + CDN access)
"""

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
from meteostat import Daily, Stations  # type: ignore[import-untyped]

from biosample_enricher.logging_config import get_logger
from biosample_enricher.weather.models import (
    TemporalPrecision,
    TemporalQuality,
    WeatherObservation,
    WeatherResult,
)
from biosample_enricher.weather.providers.base import WeatherProviderBase

logger = get_logger(__name__)


class MeteostatProvider(WeatherProviderBase):
    """
    MeteoStat weather data provider for biosample enrichment.

    Uses the meteostat Python library for keyless access to station data
    with station distance tracking and data quality assessment.
    """

    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
        self.provider_name = "meteostat"
        self.max_station_distance_km = 100  # Maximum distance to consider stations

    def get_daily_weather(
        self,
        lat: float,
        lon: float,
        target_date: date,
        _parameters: list[str] | None = None,
    ) -> WeatherResult:
        """
        Get daily weather data for specific date and location from MeteoStat.

        Uses meteostat library to find nearest station with data coverage.
        """
        logger.info(f"Fetching MeteoStat weather for ({lat}, {lon}) on {target_date}")

        try:
            # Convert date to datetime for meteostat library
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = start_dt

            # Find nearest station with data coverage for this date
            stations = Stations().nearby(lat, lon).inventory("daily", start_dt)
            station_df = stations.fetch(1)

            if station_df.empty:
                return self._create_empty_result(
                    lat,
                    lon,
                    target_date,
                    "No nearby weather stations with data coverage",
                )

            # Get station info
            station_id = station_df.index[0]
            distance_m = float(station_df["distance"].iloc[0])
            distance_km = distance_m / 1000.0

            # Check if station is within our distance limit
            if distance_km > self.max_station_distance_km:
                return self._create_empty_result(
                    lat,
                    lon,
                    target_date,
                    f"Nearest station too far: {distance_km:.1f}km",
                )

            # Fetch daily weather data
            daily_data = Daily(station_id, start_dt, end_dt)
            daily_df = daily_data.fetch()

            if daily_df.empty:
                return self._create_empty_result(
                    lat, lon, target_date, "No weather data available for date"
                )

            # Get the day's data (should be only one row)
            day_data = daily_df.iloc[0]

            # Create station info dict for compatibility
            station_info = {
                "id": station_id,
                "name": station_df.get("name", {}).get(station_id, "Unknown")
                if "name" in station_df.columns
                else "Unknown",
                "distance_km": distance_km,
                "elevation": station_df.get("elevation", {}).get(station_id, None)
                if "elevation" in station_df.columns
                else None,
            }

            # Convert to standardized WeatherResult
            weather_result = self._convert_to_weather_result(
                day_data, station_info, lat, lon, target_date
            )

            logger.info(
                f"Successfully retrieved MeteoStat weather from station {station_id} ({distance_km:.1f}km away)"
            )
            return weather_result

        except Exception as e:
            logger.error(f"MeteoStat provider failed: {e}")
            return self._create_empty_result(
                lat, lon, target_date, f"Provider error: {e}"
            )

    def _convert_to_weather_result(
        self,
        weather_data: Any,  # pandas Series from meteostat
        station_info: dict[str, Any],
        lat: float,
        lon: float,
        target_date: date,
    ) -> WeatherResult:
        """Convert MeteoStat pandas Series to standardized WeatherResult."""

        # Assess data quality based on station distance and data completeness
        distance_km = station_info["distance_km"]
        data_completeness = self._calculate_data_completeness(weather_data)

        # Determine temporal quality (station data is day-specific)
        temporal_quality = (
            TemporalQuality.DAY_SPECIFIC_COMPLETE
            if data_completeness > 0.5
            else TemporalQuality.DAY_SPECIFIC_PARTIAL
        )

        # Create temporal precision metadata
        temporal_precision = TemporalPrecision(
            method="weather_station",
            target_date=target_date.strftime("%Y-%m-%d"),
            data_quality=temporal_quality,
            coverage_info=f"Station {station_info['id']} ({distance_km:.1f}km away)",
            provider="meteostat",
        )

        # Convert weather parameters to WeatherObservation objects
        observations = {}

        # Temperature (MeteoStat provides tavg, tmin, tmax)
        temp_fields = []
        temp_data = {}

        if hasattr(weather_data, "tmin") and not pd.isna(weather_data.tmin):
            temp_data["min"] = float(weather_data.tmin)
            temp_fields.append("tmin")
        if hasattr(weather_data, "tmax") and not pd.isna(weather_data.tmax):
            temp_data["max"] = float(weather_data.tmax)
            temp_fields.append("tmax")
        if hasattr(weather_data, "tavg") and not pd.isna(weather_data.tavg):
            temp_data["avg"] = float(weather_data.tavg)
            temp_fields.append("tavg")
        elif "min" in temp_data and "max" in temp_data:
            temp_data["avg"] = (temp_data["min"] + temp_data["max"]) / 2

        if temp_data:
            observations["temperature"] = WeatherObservation(
                value=temp_data,
                unit="Celsius",
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(
                    temporal_quality, data_completeness, distance_km
                ),
            )

        # Wind speed (wspd)
        if hasattr(weather_data, "wspd") and not pd.isna(weather_data.wspd):
            observations["wind_speed"] = WeatherObservation(
                value=float(weather_data.wspd),
                unit="km/h",
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(
                    temporal_quality, data_completeness, distance_km
                ),
            )

        # Wind direction (wdir)
        if hasattr(weather_data, "wdir") and not pd.isna(weather_data.wdir):
            observations["wind_direction"] = WeatherObservation(
                value=float(weather_data.wdir),
                unit="degrees",
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(
                    temporal_quality, data_completeness, distance_km
                ),
            )

        # Precipitation (prcp)
        if hasattr(weather_data, "prcp") and not pd.isna(weather_data.prcp):
            observations["precipitation"] = WeatherObservation(
                value=float(weather_data.prcp),
                unit="mm",
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(
                    temporal_quality, data_completeness, distance_km
                ),
            )

        # Atmospheric pressure (pres)
        if hasattr(weather_data, "pres") and not pd.isna(weather_data.pres):
            observations["pressure"] = WeatherObservation(
                value=float(weather_data.pres),
                unit="hPa",
                temporal_precision=temporal_precision,
                quality_score=self._calculate_quality_score(
                    temporal_quality, data_completeness, distance_km
                ),
            )

        return WeatherResult(
            location={"lat": lat, "lon": lon},
            collection_date=target_date.strftime("%Y-%m-%d"),
            providers_attempted=["meteostat"],
            successful_providers=["meteostat"] if observations else [],
            failed_providers=[] if observations else ["meteostat"],
            overall_quality=temporal_quality,
            **observations,
        )

    def _calculate_data_completeness(self, weather_data: Any) -> float:
        """Calculate fraction of expected weather parameters that have data."""
        expected_params = ["tavg", "tmin", "tmax", "prcp", "wspd", "wdir", "pres"]
        available_params = 0

        for param in expected_params:
            if hasattr(weather_data, param):
                value = getattr(weather_data, param)
                # Check if value is not NaN
                if not pd.isna(value):
                    available_params += 1

        return available_params / len(expected_params)

    def _calculate_quality_score(
        self,
        temporal_quality: TemporalQuality,
        data_completeness: float = 1.0,
        distance_km: float = 0.0,
    ) -> int:
        """Calculate quality score based on temporal quality, data completeness, and station distance."""
        base_score = super()._calculate_quality_score(
            temporal_quality, data_completeness
        )

        # Apply distance penalty (closer stations = higher quality)
        distance_factor = max(
            0.5, 1.0 - (distance_km / self.max_station_distance_km) * 0.5
        )

        return int(base_score * distance_factor)

    def _create_empty_result(
        self, lat: float, lon: float, target_date: date, _error_msg: str
    ) -> WeatherResult:
        """Create empty WeatherResult for failed requests."""
        return WeatherResult(
            location={"lat": lat, "lon": lon},
            collection_date=target_date.strftime("%Y-%m-%d"),
            providers_attempted=["meteostat"],
            successful_providers=[],
            failed_providers=["meteostat"],
            overall_quality=TemporalQuality.NO_DATA,
        )

    def is_available(self, _lat: float, _lon: float, target_date: date) -> bool:
        """Check if MeteoStat has data for the given location and date."""
        # MeteoStat has data from 1973-present with global coverage
        start_date = date(1973, 1, 1)
        end_date = date.today() - timedelta(days=7)  # Usually 1-week lag

        return start_date <= target_date <= end_date

    def get_supported_parameters(self) -> list[str]:
        """Return list of weather parameters supported by MeteoStat."""
        return [
            "tavg",
            "tmin",
            "tmax",  # Temperature
            "prcp",  # Precipitation
            "wspd",
            "wdir",  # Wind
            "pres",  # Pressure
        ]

    def get_temporal_resolution(self) -> str:
        """Return temporal resolution."""
        return "daily"

    def get_spatial_resolution(self) -> str:
        """Return spatial resolution."""
        return "station-based"

    def get_coverage_period(self) -> dict[str, str]:
        """Return temporal coverage period."""
        return {
            "start": "1973-01-01",
            "end": "present (7-day lag)",
            "description": "Global weather station network",
        }
