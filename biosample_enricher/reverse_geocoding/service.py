"""Reverse geocoding service for coordinating multiple providers."""

from typing import Any

from ..logging_config import get_logger
from ..reverse_geocoding_models import ReverseGeocodeResult
from .providers.base import ReverseGeocodingProvider
from .providers.google import GoogleReverseGeocodingProvider
from .providers.osm import OSMReverseGeocodingProvider

logger = get_logger(__name__)


class ReverseGeocodingService:
    """Service for managing reverse geocoding providers."""

    def __init__(self) -> None:
        """Initialize the reverse geocoding service."""
        self.providers: dict[str, ReverseGeocodingProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize available reverse geocoding providers."""
        # Initialize OSM provider (always available)
        try:
            osm_provider = OSMReverseGeocodingProvider()
            self.providers["osm"] = osm_provider
            logger.info("Initialized OSM reverse geocoding provider")
        except Exception as e:
            logger.error(f"Failed to initialize OSM provider: {e}")

        # Initialize Google provider if API key is available
        try:
            google_provider = GoogleReverseGeocodingProvider()
            self.providers["google"] = google_provider
            logger.info("Initialized Google reverse geocoding provider")
        except ValueError as e:
            logger.warning(f"Google provider not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Google provider: {e}")

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())

    def get_provider(self, name: str) -> ReverseGeocodingProvider | None:
        """
        Get a specific provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None if not found
        """
        return self.providers.get(name)

    def reverse_geocode(
        self,
        lat: float,
        lon: float,
        provider: str | None = None,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
        language: str = "en",
        limit: int = 10,
    ) -> ReverseGeocodeResult | None:
        """
        Perform reverse geocoding using specified or default provider.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            provider: Provider name (None for auto-selection)
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results
            limit: Maximum number of results

        Returns:
            Reverse geocoding result or None if failed
        """
        # Select provider
        if provider:
            provider_instance = self.providers.get(provider)
            if not provider_instance:
                logger.error(f"Provider '{provider}' not found")
                return None
        else:
            # Auto-select: prefer Google if available, else OSM
            provider_instance = self.providers.get("google") or self.providers.get(
                "osm"
            )
            if not provider_instance:
                logger.error("No providers available")
                return None

        # Perform reverse geocoding
        try:
            logger.info(
                f"Reverse geocoding {lat:.6f}, {lon:.6f} using {provider_instance.name}"
            )

            result = provider_instance.fetch(
                lat,
                lon,
                read_from_cache=read_from_cache,
                write_to_cache=write_to_cache,
                timeout_s=timeout_s,
                language=language,
                limit=limit,
            )

            if result.ok and result.result:
                return result.result
            else:
                logger.error(f"Reverse geocoding failed: {result.error}")
                return None

        except Exception as e:
            logger.error(f"Error during reverse geocoding: {e}")
            return None

    def reverse_geocode_multiple(
        self,
        lat: float,
        lon: float,
        providers: list[str] | None = None,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
        language: str = "en",
        limit: int = 10,
    ) -> dict[str, ReverseGeocodeResult]:
        """
        Perform reverse geocoding using multiple providers sequentially.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            providers: List of provider names (None for all available)
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results
            limit: Maximum number of results per provider

        Returns:
            Dictionary mapping provider names to results
        """
        # Select providers
        if providers:
            provider_instances = {
                name: self.providers[name]
                for name in providers
                if name in self.providers
            }
        else:
            provider_instances = dict(self.providers.items())

        if not provider_instances:
            logger.error("No providers available")
            return {}

        # Execute providers sequentially
        output: dict[str, ReverseGeocodeResult] = {}
        for name, provider_instance in provider_instances.items():
            try:
                fetch_result = provider_instance.fetch(
                    lat,
                    lon,
                    read_from_cache=read_from_cache,
                    write_to_cache=write_to_cache,
                    timeout_s=timeout_s,
                    language=language,
                    limit=limit,
                )

                if fetch_result.ok and fetch_result.result:
                    output[name] = fetch_result.result
                else:
                    logger.error(f"Provider {name} failed: {fetch_result.error}")

            except Exception as e:
                logger.error(f"Provider {name} failed with exception: {e}")

        return output

    def compare_providers(
        self,
        lat: float,
        lon: float,
        *,
        language: str = "en",
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Compare results from all available providers.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            language: Language code for results
            limit: Maximum number of results per provider

        Returns:
            Comparison dictionary with results and analysis
        """
        # Get results from all providers
        results = self.reverse_geocode_multiple(
            lat, lon, language=language, limit=limit
        )

        if not results:
            return {"error": "No providers returned results"}

        # Extract best matches from each provider
        comparison: dict[str, Any] = {
            "query": {"lat": lat, "lon": lon},
            "providers": {},
            "consensus": {},
        }

        # Process each provider's results
        for provider_name, result in results.items():
            best_match = result.get_best_match()
            if best_match:
                comparison["providers"][provider_name] = {
                    "formatted_address": best_match.formatted_address,
                    "country": best_match.country,
                    "country_code": best_match.country_code,
                    "state": best_match.state,
                    "city": best_match.city,
                    "postcode": best_match.postcode,
                    "confidence": best_match.confidence,
                    "distance_m": best_match.distance_m,
                    "response_time_ms": result.response_time_ms,
                    "cache_hit": result.cache_hit,
                    "num_results": len(result.locations),
                }

        # Find consensus values (values that appear in multiple providers)
        fields_to_compare = ["country", "country_code", "state", "city", "postcode"]
        for field in fields_to_compare:
            values: dict[str, list[str]] = {}
            for provider_name, provider_data in comparison["providers"].items():
                value = provider_data.get(field)
                if value:
                    if value not in values:
                        values[value] = []
                    values[value].append(provider_name)

            # Find most common value
            if values:
                most_common = max(values.items(), key=lambda x: len(x[1]))
                comparison["consensus"][field] = {
                    "value": most_common[0],
                    "providers": most_common[1],
                    "agreement": len(most_common[1]) / len(results),
                }

        return comparison
