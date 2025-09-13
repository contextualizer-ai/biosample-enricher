"""Abstract base class for forward geocoding providers."""

from abc import ABC, abstractmethod

from biosample_enricher.forward_geocoding.models import ForwardGeocodeFetchResult


class ForwardGeocodingProvider(ABC):
    """Abstract base class for forward geocoding providers (place name to coordinates)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for identification."""
        pass

    @property
    @abstractmethod
    def attribution(self) -> str | None:
        """Required attribution text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API key, network, etc.)."""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        _read_from_cache: bool = True,
        _write_to_cache: bool = True,
        timeout_s: float = 30.0,
        language: str = "en",
        country_codes: list[str] | None = None,
        max_results: int = 10,
    ) -> ForwardGeocodeFetchResult:
        """
        Perform forward geocoding to convert place names to coordinates.

        Args:
            query: Place name or address to search for
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language for results (ISO 639-1 code)
            country_codes: List of ISO country codes to restrict search
            max_results: Maximum number of results to return

        Returns:
            Forward geocoding fetch result
        """
        pass

    def validate_query(self, query: str) -> None:
        """Validate place name query input."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if len(query.strip()) < 2:
            raise ValueError("Query must be at least 2 characters long")
