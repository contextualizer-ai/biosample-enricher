"""Abstract base classes for land cover and vegetation data providers."""

from abc import ABC, abstractmethod
from datetime import date

from biosample_enricher.land.models import LandCoverObservation, VegetationObservation


class LandCoverProviderBase(ABC):
    """Abstract base class for land cover data providers."""

    @abstractmethod
    def get_land_cover(
        self, latitude: float, longitude: float, target_date: date | None = None
    ) -> list[LandCoverObservation]:
        """Retrieve land cover data for a specific location and date.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Target date for land cover data

        Returns:
            List of land cover observations (may be empty if no data)

        Raises:
            ValueError: If coordinates are invalid
            RuntimeError: If the provider is unavailable
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is currently available.

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for identification and logging."""
        pass

    @property
    @abstractmethod
    def coverage_description(self) -> str:
        """Description of geographic and temporal coverage."""
        pass

    def validate_coordinates(self, latitude: float, longitude: float) -> None:
        """Validate coordinate inputs.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Raises:
            ValueError: If coordinates are invalid
        """
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")

        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")


class VegetationProviderBase(ABC):
    """Abstract base class for vegetation index data providers."""

    @abstractmethod
    def get_vegetation_indices(
        self,
        latitude: float,
        longitude: float,
        target_date: date | None = None,
        time_window_days: int = 16,
    ) -> list[VegetationObservation]:
        """Retrieve vegetation indices for a specific location and date.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Target date for vegetation data
            time_window_days: Search window around target date (days)

        Returns:
            List of vegetation observations (may be empty if no data)

        Raises:
            ValueError: If coordinates are invalid
            RuntimeError: If the provider is unavailable
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is currently available.

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for identification and logging."""
        pass

    @property
    @abstractmethod
    def coverage_description(self) -> str:
        """Description of geographic and temporal coverage."""
        pass

    def validate_coordinates(self, latitude: float, longitude: float) -> None:
        """Validate coordinate inputs.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Raises:
            ValueError: If coordinates are invalid
        """
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")

        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")

    def calculate_temporal_offset(self, target_date: date, actual_date: date) -> int:
        """Calculate temporal offset between target and actual dates.

        Args:
            target_date: Requested date
            actual_date: Actual data date

        Returns:
            Number of days difference (positive if actual is after target)
        """
        return (actual_date - target_date).days

    def calculate_spatial_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in meters
        """
        import math

        R = 6371000.0  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
