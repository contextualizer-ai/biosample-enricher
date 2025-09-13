"""Abstract base class for soil data providers."""

from abc import ABC, abstractmethod

from biosample_enricher.soil.models import SoilResult


class SoilProviderBase(ABC):
    """Abstract base class for soil data providers.

    All soil providers must implement this interface to ensure
    consistent behavior and error handling.
    """

    @abstractmethod
    def get_soil_data(
        self, latitude: float, longitude: float, depth_cm: str | None = "0-5cm"
    ) -> SoilResult:
        """Retrieve soil data for a specific location.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            depth_cm: Depth interval (e.g., "0-5cm", "5-15cm")

        Returns:
            SoilResult with observations and quality metrics

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
        """Description of geographic and data coverage."""
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

    def calculate_quality_score(
        self,
        distance_m: float | None = None,
        confidence: float | None = None,
        data_completeness: float = 1.0,
    ) -> float:
        """Calculate overall data quality score.

        Args:
            distance_m: Distance from requested location to measurement (meters)
            confidence: Provider-specific confidence score (0-1)
            data_completeness: Fraction of requested data fields available (0-1)

        Returns:
            Quality score from 0.0 (poor) to 1.0 (excellent)
        """
        score = 1.0

        # Distance penalty: reduce score for distant measurements
        if distance_m is not None:
            if distance_m <= 100:  # Within 100m = excellent
                distance_score = 1.0
            elif distance_m <= 1000:  # Within 1km = good
                distance_score = 0.9
            elif distance_m <= 5000:  # Within 5km = fair
                distance_score = 0.7
            elif distance_m <= 25000:  # Within 25km = poor
                distance_score = 0.5
            else:  # Beyond 25km = very poor
                distance_score = 0.3
            score *= distance_score

        # Provider confidence penalty
        if confidence is not None:
            score *= confidence

        # Data completeness penalty
        score *= data_completeness

        return max(0.0, min(1.0, score))
