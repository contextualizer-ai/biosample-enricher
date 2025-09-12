"""Base class for marine data providers."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from biosample_enricher.marine.models import MarineResult


class MarineProviderBase(ABC):
    """Abstract base class for marine data providers."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize provider with timeout setting.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name."""
        pass

    @abstractmethod
    def get_provider_info(self) -> dict[str, Any]:
        """Get provider metadata and capabilities.

        Returns:
            Dictionary with provider information
        """
        pass

    @abstractmethod
    def get_coverage_period(self) -> dict[str, str]:
        """Get temporal coverage of the provider.

        Returns:
            Dictionary with start and end dates
        """
        pass

    @abstractmethod
    def is_available(
        self, latitude: float, longitude: float, target_date: date
    ) -> bool:
        """Check if provider has data for given location and date.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date for data query

        Returns:
            True if data is available
        """
        pass

    @abstractmethod
    def get_marine_data(
        self,
        latitude: float,
        longitude: float,
        target_date: date,
        parameters: list[str] | None = None,
    ) -> MarineResult:
        """Get marine data for location and date.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date for data query
            parameters: Optional list of specific parameters to retrieve

        Returns:
            MarineResult with oceanographic data
        """
        pass

    def _validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Validate coordinate ranges.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            True if coordinates are valid
        """
        return -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0

    def _is_marine_location(self, _latitude: float, _longitude: float) -> bool:
        """Check if coordinates are likely in marine environment.

        This is a basic check - providers can override with more sophisticated logic.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            True if location appears to be marine
        """
        # Basic ocean coverage check - can be refined by individual providers
        # This is just a placeholder - real marine detection would use coastline data
        return True
