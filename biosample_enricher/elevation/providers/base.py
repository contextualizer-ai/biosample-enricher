"""Base class and protocol for elevation providers."""

from abc import ABC, abstractmethod
from typing import Protocol

from ...logging_config import get_logger
from ...models import FetchResult

logger = get_logger(__name__)


class ElevationProvider(Protocol):
    """Protocol defining the interface for elevation providers."""

    name: str
    endpoint: str
    api_version: str

    async def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
    ) -> FetchResult:
        """
        Fetch elevation data for the given coordinates.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds

        Returns:
            Fetch result with elevation data
        """
        ...


class BaseElevationProvider(ABC):
    """Base implementation for elevation providers."""

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
    async def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
    ) -> FetchResult:
        """
        Fetch elevation data for the given coordinates.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds

        Returns:
            Fetch result with elevation data
        """
        pass

    def _create_cache_key(self, lat: float, lon: float) -> str:
        """
        Create a cache key for the given coordinates.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Cache key string
        """
        # Canonicalize coordinates to 6 decimal places
        return f"{self.name}:{lat:.6f},{lon:.6f}"

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
