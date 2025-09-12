"""
Base weather provider interface for standardized weather data access.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from ..models import TemporalQuality, WeatherResult


class WeatherProviderBase(ABC):
    """
    Abstract base class for weather data providers.

    Defines the interface that all weather providers must implement for
    consistent biosample enrichment workflows.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    def get_daily_weather(
        self, lat: float, lon: float, target_date: date, parameters: list | None = None
    ) -> WeatherResult:
        """
        Get weather data for a specific date and location.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            target_date: Date for weather lookup
            parameters: Optional list of specific parameters to fetch

        Returns:
            WeatherResult with standardized observations
        """
        pass

    @abstractmethod
    def is_available(self, lat: float, lon: float, target_date: date) -> bool:
        """
        Check if provider has data available for given location and date.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            target_date: Date to check availability

        Returns:
            True if data is available, False otherwise
        """
        pass

    def get_provider_info(self) -> dict[str, Any]:
        """
        Get provider metadata and capabilities.

        Returns:
            Dict with provider information
        """
        return {
            "name": self.provider_name,
            "timeout": self.timeout,
            "parameters_supported": self.get_supported_parameters(),
            "temporal_resolution": self.get_temporal_resolution(),
            "spatial_resolution": self.get_spatial_resolution(),
            "coverage_period": self.get_coverage_period(),
        }

    @abstractmethod
    def get_supported_parameters(self) -> list:
        """Return list of weather parameters this provider supports."""
        pass

    @abstractmethod
    def get_temporal_resolution(self) -> str:
        """Return temporal resolution (e.g., 'hourly', 'daily')."""
        pass

    @abstractmethod
    def get_spatial_resolution(self) -> str:
        """Return spatial resolution (e.g., '11km', 'station-based')."""
        pass

    @abstractmethod
    def get_coverage_period(self) -> dict[str, str]:
        """Return temporal coverage period."""
        pass

    def _assess_temporal_quality(
        self,
        _target_date: date,
        available_hours: int,
        total_hours: int = 24,
        method: str = "unknown",
    ) -> TemporalQuality:
        """
        Assess temporal data quality based on coverage.

        Args:
            target_date: Target date for weather lookup
            available_hours: Number of hours with data available
            total_hours: Total hours in period (default 24 for daily)
            method: Data acquisition method

        Returns:
            TemporalQuality enum value
        """
        coverage_fraction = available_hours / total_hours

        if coverage_fraction >= 0.8:  # 80%+ coverage
            return TemporalQuality.DAY_SPECIFIC_COMPLETE
        elif coverage_fraction >= 0.5:  # 50-79% coverage
            return TemporalQuality.DAY_SPECIFIC_PARTIAL
        elif "weekly" in method.lower():
            return TemporalQuality.WEEKLY_COMPOSITE
        elif "monthly" in method.lower() or "climatology" in method.lower():
            return TemporalQuality.MONTHLY_CLIMATOLOGY
        else:
            return TemporalQuality.NO_DATA

    def _calculate_quality_score(
        self, temporal_quality: TemporalQuality, data_completeness: float = 1.0
    ) -> int:
        """
        Calculate 0-100 quality score based on temporal quality and data completeness.

        Args:
            temporal_quality: TemporalQuality assessment
            data_completeness: Fraction of parameters successfully retrieved (0.0-1.0)

        Returns:
            Quality score from 0-100
        """
        base_scores = {
            TemporalQuality.DAY_SPECIFIC_COMPLETE: 100,
            TemporalQuality.DAY_SPECIFIC_PARTIAL: 85,
            TemporalQuality.WEEKLY_COMPOSITE: 70,
            TemporalQuality.MONTHLY_CLIMATOLOGY: 50,
            TemporalQuality.NO_DATA: 0,
        }

        base_score = base_scores.get(temporal_quality, 0)
        return int(base_score * data_completeness)
