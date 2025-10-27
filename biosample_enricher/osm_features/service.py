"""OSM geographic features enrichment service."""

from typing import Any

from biosample_enricher.logging_config import get_logger
from biosample_enricher.osm_features.google_provider import GooglePlacesProvider
from biosample_enricher.osm_features.models import (
    CombinedFeaturesResult,
    Coordinates,
    OSMFeaturesResult,
)
from biosample_enricher.osm_features.provider import OSMOverpassProvider

logger = get_logger(__name__)


class OSMFeaturesService:
    """Service for enriching locations with geographic features from multiple providers."""

    def __init__(self, default_radius_m: int = 1000, enable_google: bool = True):
        """
        Initialize geographic features service.

        Args:
            default_radius_m: Default search radius in meters
            enable_google: Whether to enable Google Places provider if available
        """
        self.default_radius_m = default_radius_m
        self.osm_provider = OSMOverpassProvider()

        # Initialize Google provider if enabled
        self.google_provider = None
        if enable_google:
            try:
                self.google_provider = GooglePlacesProvider()
                if not self.google_provider.is_available():
                    logger.info("Google Places API not available, using OSM only")
                    self.google_provider = None
            except Exception as e:
                logger.warning(f"Failed to initialize Google Places provider: {e}")
                self.google_provider = None

    def get_combined_features_for_location(
        self,
        latitude: float,
        longitude: float,
        radius_m: int | None = None,
        timeout_s: int = 180,
    ) -> CombinedFeaturesResult:
        """
        Get geographic features from both OSM and Google Places providers.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_m: Search radius in meters (uses default if None)
            timeout_s: Query timeout in seconds

        Returns:
            Combined features result from both providers
        """
        if radius_m is None:
            radius_m = self.default_radius_m

        logger.info(
            f"Getting combined features for {latitude}, {longitude} within {radius_m}m"
        )

        query_coords = Coordinates(latitude=latitude, longitude=longitude)
        providers_successful = []
        providers_failed = []
        osm_result = None
        google_result = None

        # Query OSM provider
        try:
            osm_fetch = self.osm_provider.get_features(
                latitude=latitude,
                longitude=longitude,
                radius_m=radius_m,
                timeout_s=timeout_s,
            )
            if osm_fetch.ok and osm_fetch.result:
                osm_result = osm_fetch.result
                providers_successful.append("osm")
                logger.info(
                    f"OSM: Found {len(osm_result.named_features)} named features"
                )
            else:
                providers_failed.append("osm")
                logger.warning(f"OSM provider failed: {osm_fetch.error}")
        except Exception as e:
            providers_failed.append("osm")
            logger.error(f"OSM provider error: {e}")

        # Query Google Places provider if available
        if self.google_provider:
            try:
                google_fetch = self.google_provider.get_features(
                    latitude=latitude,
                    longitude=longitude,
                    radius_m=radius_m,
                    timeout_s=timeout_s,
                )
                if google_fetch.ok and google_fetch.result:
                    google_result = google_fetch.result
                    providers_successful.append("google_places")
                    logger.info(
                        f"Google Places: Found {len(google_result.named_features)} named features"
                    )
                else:
                    providers_failed.append("google_places")
                    logger.warning(
                        f"Google Places provider failed: {google_fetch.error}"
                    )
            except Exception as e:
                providers_failed.append("google_places")
                logger.error(f"Google Places provider error: {e}")
        else:
            logger.debug("Google Places provider not available")

        # Create combined result
        combined_success = len(providers_successful) > 0

        return CombinedFeaturesResult(
            query=query_coords,
            radius_m=radius_m,
            osm_result=osm_result,
            google_result=google_result,
            providers_successful=providers_successful,
            providers_failed=providers_failed,
            combined_enrichment_success=combined_success,
        )

    def get_features_for_location(
        self,
        latitude: float,
        longitude: float,
        radius_m: int | None = None,
        timeout_s: int = 180,
    ) -> OSMFeaturesResult | None:
        """
        Get geographic features around a location from OSM only (for backward compatibility).

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_m: Search radius in meters (uses default if None)
            timeout_s: Query timeout in seconds

        Returns:
            OSM features result or None if failed
        """
        if radius_m is None:
            radius_m = self.default_radius_m

        logger.info(
            f"Getting OSM features for {latitude}, {longitude} within {radius_m}m"
        )

        # Check provider availability
        if not self.osm_provider.is_available():
            logger.warning("OSM Overpass API is not available")
            return None

        # Get features from provider
        fetch_result = self.osm_provider.get_features(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            timeout_s=timeout_s,
        )

        if not fetch_result.ok:
            logger.error(f"OSM features enrichment failed: {fetch_result.error}")
            return None

        result = fetch_result.result
        if result:
            logger.info(
                f"Found {result.named_features_count} named features and "
                f"{result.unnamed_categories_count} categories of unnamed features"
            )

            # Log some key findings
            if result.named_features:
                nearest = result.named_features[0]
                logger.info(
                    f"Nearest named feature: {nearest.name} ({nearest.category.value}) "
                    f"at {nearest.distance_km:.3f}km"
                )

        return result

    def enrich_biosample_location(
        self,
        latitude: float,
        longitude: float,
        radius_m: int | None = None,
        timeout_s: int = 180,
        use_combined: bool = True,
    ) -> dict[str, Any]:
        """
        Enrich a biosample location with geographic features from multiple providers.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_m: Search radius in meters (uses default if None)
            timeout_s: Query timeout in seconds
            use_combined: Whether to use combined providers (True) or OSM only (False)

        Returns:
            Dictionary suitable for biosample enrichment
        """
        if radius_m is None:
            radius_m = self.default_radius_m

        if use_combined:
            # Use combined features from both providers
            combined_result = self.get_combined_features_for_location(
                latitude=latitude,
                longitude=longitude,
                radius_m=radius_m,
                timeout_s=timeout_s,
            )

            if not combined_result.combined_enrichment_success:
                return {
                    "features_enrichment_success": False,
                    "features_error": "All geographic feature providers failed",
                    "features_providers_failed": combined_result.providers_failed,
                }

            # Convert to enrichment dictionary
            enrichment = combined_result.to_enrichment_dict()
            return enrichment
        else:
            # Use OSM only for backward compatibility
            osm_result = self.get_features_for_location(
                latitude=latitude,
                longitude=longitude,
                radius_m=radius_m,
                timeout_s=timeout_s,
            )

            if not osm_result:
                return {
                    "osm_features_found": 0,
                    "osm_enrichment_success": False,
                    "osm_error": "Failed to retrieve OSM features",
                }

            # Convert to enrichment dictionary
            enrichment = osm_result.to_enrichment_dict()
            enrichment["osm_enrichment_success"] = True
            return enrichment

    def get_features_for_biosample(
        self, biosample: dict[str, Any], radius_m: int = 1000, timeout_s: int = 180
    ) -> dict[str, Any]:
        """
        Get OSM features for a biosample dictionary.

        Args:
            biosample: Biosample data dictionary
            radius_m: Search radius in meters
            timeout_s: Query timeout in seconds

        Returns:
            Enrichment result dictionary
        """
        # Extract coordinates from biosample
        coords = self._extract_coordinates(biosample)
        if not coords:
            return {
                "osm_features_found": 0,
                "osm_enrichment_success": False,
                "osm_error": "No coordinates available",
            }

        latitude, longitude = coords
        return self.enrich_biosample_location(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            timeout_s=timeout_s,
        )

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all geographic features providers."""
        status = {}

        # OSM Overpass API status
        osm_available = self.osm_provider.is_available()
        status["osm_overpass"] = {
            "name": "OpenStreetMap Overpass API",
            "available": osm_available,
            "attribution": "© OpenStreetMap contributors",
            "base_url": self.osm_provider.base_url,
            "rate_limit": "1 request per second",
            "error": None if osm_available else "Service not responding",
        }

        # Google Places API status
        if self.google_provider:
            google_available = self.google_provider.is_available()
            status["google_places"] = {
                "name": "Google Places API",
                "available": google_available,
                "attribution": "Powered by Google",
                "base_url": self.google_provider.base_url,
                "rate_limit": "1000 requests per day (free tier)",
                "error": None
                if google_available
                else "API key invalid or quota exceeded",
            }
        else:
            status["google_places"] = {
                "name": "Google Places API",
                "available": False,
                "attribution": "Powered by Google",
                "base_url": "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                "rate_limit": "1000 requests per day (free tier)",
                "error": "API key not provided or initialization failed",
            }

        return status

    def _extract_coordinates(
        self, biosample: dict[str, Any]
    ) -> tuple[float, float] | None:
        """Extract coordinates from biosample data."""
        # Try different coordinate field patterns
        coordinate_patterns = [
            # Direct lat/lon fields
            ("latitude", "longitude"),
            ("lat", "lon"),
            ("lat", "lng"),
            # Nested location objects
            ("location.latitude", "location.longitude"),
            ("coordinates.latitude", "coordinates.longitude"),
            ("geo_loc.latitude", "geo_loc.longitude"),
            # Array format [lat, lon]
            ("coordinates",),
        ]

        for pattern in coordinate_patterns:
            if len(pattern) == 2:
                lat_field, lon_field = pattern
                lat = self._get_nested_value(biosample, lat_field)
                lon = self._get_nested_value(biosample, lon_field)

                if lat is not None and lon is not None:
                    try:
                        lat_val = float(lat)
                        lon_val = float(lon)
                        if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                            return lat_val, lon_val
                    except (ValueError, TypeError):
                        continue

            elif len(pattern) == 1:
                coords_field = pattern[0]
                coords = self._get_nested_value(biosample, coords_field)

                if isinstance(coords, list | tuple) and len(coords) >= 2:
                    try:
                        lat_val = float(coords[0])
                        lon_val = float(coords[1])
                        if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                            return lat_val, lon_val
                    except (ValueError, TypeError, IndexError):
                        continue

        return None

    def _get_nested_value(self, data: dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = field_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def batch_enrich_locations(
        self,
        locations: list[tuple[float, float]],
        radius_m: int = 1000,
        timeout_s: int = 180,
    ) -> list[dict[str, Any]]:
        """
        Batch enrich multiple locations with OSM features.

        Args:
            locations: List of (latitude, longitude) tuples
            radius_m: Search radius in meters
            timeout_s: Query timeout in seconds per location

        Returns:
            List of enrichment dictionaries
        """
        results = []

        for i, (lat, lon) in enumerate(locations):
            if i % 10 == 0:
                logger.info(f"Processing location {i + 1}/{len(locations)}")

            try:
                enrichment = self.enrich_biosample_location(
                    latitude=lat,
                    longitude=lon,
                    radius_m=radius_m,
                    timeout_s=timeout_s,
                )
                enrichment["location_index"] = i
                results.append(enrichment)

            except Exception as e:
                logger.error(f"Error enriching location {i}: {e}")
                results.append(
                    {
                        "location_index": i,
                        "osm_features_found": 0,
                        "osm_enrichment_success": False,
                        "osm_error": str(e),
                    }
                )

        return results
