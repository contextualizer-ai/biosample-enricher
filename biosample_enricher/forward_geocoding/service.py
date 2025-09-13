"""Forward geocoding service for coordinating multiple providers (place names to coordinates)."""

from typing import Any

from biosample_enricher.forward_geocoding.models import ForwardGeocodeResult
from biosample_enricher.forward_geocoding.providers.base import ForwardGeocodingProvider
from biosample_enricher.forward_geocoding.providers.google import (
    GoogleForwardGeocodingProvider,
)
from biosample_enricher.forward_geocoding.providers.osm import (
    OSMForwardGeocodingProvider,
)
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class ForwardGeocodingService:
    """Service for managing forward geocoding providers (place names to coordinates)."""

    def __init__(self) -> None:
        """Initialize the forward geocoding service."""
        self.providers: dict[str, ForwardGeocodingProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize available forward geocoding providers."""
        # Initialize OSM provider (always available)
        try:
            osm_provider = OSMForwardGeocodingProvider()
            self.providers["osm"] = osm_provider
            logger.info("Initialized OSM forward geocoding provider")
        except Exception as e:
            logger.error(f"Failed to initialize OSM provider: {e}")

        # Initialize Google provider if API key is available
        try:
            google_provider = GoogleForwardGeocodingProvider()
            self.providers["google"] = google_provider
            logger.info("Initialized Google forward geocoding provider")
        except ValueError as e:
            logger.warning(f"Google provider not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Google provider: {e}")

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())

    def get_provider(self, name: str) -> ForwardGeocodingProvider | None:
        """Get a specific provider by name."""
        return self.providers.get(name)

    def get_provider_status(self) -> dict[str, dict[str, Any]]:
        """Get status information for all providers."""
        status = {}

        for name, provider in self.providers.items():
            try:
                available = provider.is_available()
                status[name] = {
                    "name": provider.name,
                    "available": available,
                    "attribution": provider.attribution,
                    "error": None,
                }
            except Exception as e:
                status[name] = {
                    "name": getattr(provider, "name", name),
                    "available": False,
                    "attribution": getattr(provider, "attribution", None),
                    "error": str(e),
                }

        return status

    def geocode(
        self,
        query: str,
        provider: str | None = None,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 30.0,
        language: str = "en",
        country_codes: list[str] | None = None,
        max_results: int = 10,
    ) -> ForwardGeocodeResult | None:
        """
        Perform forward geocoding to convert place name to coordinates.

        Args:
            query: Place name or address to search for
            provider: Provider name (None for auto-selection)
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results
            country_codes: List of ISO country codes to restrict search
            max_results: Maximum number of results

        Returns:
            Forward geocoding result or None if failed
        """
        if not query or not query.strip():
            logger.warning("Empty geocoding query provided")
            return None

        # Auto-select provider if not specified
        if provider is None:
            provider = self._select_best_provider()

        if provider not in self.providers:
            logger.error(f"Provider '{provider}' not available")
            return None

        geocoding_provider = self.providers[provider]

        # Check if provider is available
        if not geocoding_provider.is_available():
            logger.warning(f"Provider '{provider}' is not available, trying fallback")
            # Try fallback provider
            fallback_provider = self._get_fallback_provider(provider)
            if fallback_provider and fallback_provider in self.providers:
                geocoding_provider = self.providers[fallback_provider]
                provider = fallback_provider
            else:
                logger.error("No available providers for forward geocoding")
                return None

        try:
            logger.info(f"Forward geocoding '{query}' using {provider}")

            # Perform search
            fetch_result = geocoding_provider.search(
                query,
                _read_from_cache=read_from_cache,
                _write_to_cache=write_to_cache,
                timeout_s=timeout_s,
                language=language,
                country_codes=country_codes,
                max_results=max_results,
            )

            if not fetch_result.ok:
                logger.error(f"Forward geocoding failed: {fetch_result.error}")
                return None

            return fetch_result.result

        except Exception as e:
            logger.error(f"Forward geocoding error with {provider}: {e}")
            return None

    def geocode_multiple(
        self,
        query: str,
        providers: list[str] | None = None,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 30.0,
        language: str = "en",
        country_codes: list[str] | None = None,
        max_results: int = 5,
    ) -> dict[str, ForwardGeocodeResult]:
        """
        Perform forward geocoding using multiple providers for comparison.

        Args:
            query: Place name or address to search for
            providers: List of provider names (None for all available)
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results
            country_codes: List of ISO country codes to restrict search
            max_results: Maximum results per provider

        Returns:
            Dictionary mapping provider names to results
        """
        if providers is None:
            providers = self.get_available_providers()

        results = {}

        for provider_name in providers:
            if provider_name not in self.providers:
                logger.warning(f"Provider '{provider_name}' not available")
                continue

            try:
                result = self.geocode(
                    query,
                    provider=provider_name,
                    read_from_cache=read_from_cache,
                    write_to_cache=write_to_cache,
                    timeout_s=timeout_s,
                    language=language,
                    country_codes=country_codes,
                    max_results=max_results,
                )

                if result:
                    results[provider_name] = result

            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                continue

        return results

    def get_coordinates_for_place(
        self,
        place_name: str,
        prefer_provider: str | None = None,
        language: str = "en",
        country_hint: str | None = None,
    ) -> dict[str, Any]:
        """
        Get coordinates and enrichment data for a biosample place name.

        This is the main method for biosample enrichment - converts place names
        from metadata into precise coordinates.

        Args:
            place_name: Name of place/location from biosample metadata
            prefer_provider: Preferred provider name
            language: Language code for results
            country_hint: ISO country code hint for better results

        Returns:
            Dictionary with coordinates and administrative information
        """
        if not place_name or not place_name.strip():
            return {}

        country_codes = [country_hint] if country_hint else None

        # Try multiple providers to get best results
        providers_to_try = []
        if prefer_provider and prefer_provider in self.providers:
            providers_to_try.append(prefer_provider)

        # Add other providers as fallbacks
        for provider in ["google", "osm"]:
            if provider != prefer_provider and provider in self.providers:
                providers_to_try.append(provider)

        enrichment_data = {}
        errors = []

        for provider_name in providers_to_try:
            try:
                result = self.geocode(
                    place_name,
                    provider=provider_name,
                    language=language,
                    country_codes=country_codes,
                    max_results=1,  # Just need the best match
                )

                if result and result.locations:
                    # Get enrichment data from best match
                    enrichment_data = result.to_enrichment_dict()
                    enrichment_data["providers_attempted"] = providers_to_try
                    enrichment_data["providers_successful"] = [provider_name]

                    logger.info(
                        f"Successfully geocoded '{place_name}' using {provider_name}"
                    )
                    return enrichment_data

            except Exception as e:
                error_msg = f"{provider_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(
                    f"Provider {provider_name} failed for '{place_name}': {e}"
                )
                continue

        # No successful geocoding
        logger.warning(f"Failed to geocode '{place_name}' with any provider")
        return {
            "providers_attempted": providers_to_try,
            "providers_successful": [],
            "errors": errors,
        }

    def _select_best_provider(self) -> str:
        """Select the best available provider."""
        # Prefer Google if available (more accurate), fallback to OSM
        if "google" in self.providers:
            try:
                if self.providers["google"].is_available():
                    return "google"
            except Exception:
                pass

        if "osm" in self.providers:
            try:
                if self.providers["osm"].is_available():
                    return "osm"
            except Exception:
                pass

        # Return first available provider as last resort
        for name, provider in self.providers.items():
            try:
                if provider.is_available():
                    return name
            except Exception:
                continue

        raise RuntimeError("No forward geocoding providers available")

    def _get_fallback_provider(self, primary_provider: str) -> str | None:
        """Get fallback provider if primary fails."""
        if primary_provider == "google":
            return "osm"
        elif primary_provider == "osm":
            return "google"
        else:
            # For any other provider, try google first, then osm
            if "google" in self.providers:
                return "google"
            elif "osm" in self.providers:
                return "osm"
            return None
