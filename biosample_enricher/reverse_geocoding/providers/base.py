"""Base class and protocol for reverse geocoding providers."""

from abc import ABC, abstractmethod
from typing import Protocol

from ...logging_config import get_logger
from ...reverse_geocoding_models import ReverseGeocodeFetchResult

logger = get_logger(__name__)


class ReverseGeocodingProvider(Protocol):
    """Protocol defining the interface for reverse geocoding providers."""

    name: str
    endpoint: str
    api_version: str

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
        language: str = "en",
        limit: int = 10,
    ) -> ReverseGeocodeFetchResult:
        """
        Fetch reverse geocoding data for the given coordinates.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results (ISO 639-1)
            limit: Maximum number of results to return

        Returns:
            Fetch result with reverse geocoding data
        """
        ...


class BaseReverseGeocodingProvider(ABC):
    """Base implementation for reverse geocoding providers."""

    def __init__(self, name: str, endpoint: str, api_version: str = "v1") -> None:
        """
        Initialize the provider.

        Args:
            name: Provider name
            endpoint: API endpoint URL
            api_version: API version
        """
        self.name = name
        self.endpoint = endpoint
        self.api_version = api_version
        logger.debug(f"Initialized {name} provider: {endpoint}")

    @abstractmethod
    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
        language: str = "en",
        limit: int = 10,
    ) -> ReverseGeocodeFetchResult:
        """
        Fetch reverse geocoding data for the given coordinates.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results (ISO 639-1)
            limit: Maximum number of results to return

        Returns:
            Fetch result with reverse geocoding data
        """
        pass

    def _create_cache_key(
        self, lat: float, lon: float, language: str = "en", limit: int = 10
    ) -> str:
        """
        Create a cache key for the given coordinates and parameters.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            language: Language code
            limit: Result limit

        Returns:
            Cache key string
        """
        # Canonicalize coordinates to 6 decimal places
        return f"{self.name}:reverse:{lat:.6f},{lon:.6f}:{language}:{limit}"

    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """
        Validate coordinate ranges.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Raises:
            ValueError: If coordinates are out of valid range
        """
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")

        if not -180.0 <= lon <= 180.0:
            raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180.")
