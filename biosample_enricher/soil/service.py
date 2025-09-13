"""Soil enrichment service orchestration."""

from typing import Any

from biosample_enricher.logging_config import get_logger
from biosample_enricher.soil.models import SoilResult
from biosample_enricher.soil.providers.soilgrids import SoilGridsProvider
from biosample_enricher.soil.providers.usda_nrcs import USDANRCSProvider

logger = get_logger(__name__)


class SoilService:
    """Multi-provider soil enrichment service.

    Orchestrates multiple soil data providers with intelligent cascading:
    - US locations: USDA NRCS SDA primary, SoilGrids fallback
    - Global locations: SoilGrids primary

    Provides static soil site characterization including taxonomy,
    properties, and texture classification.
    """

    def __init__(self):
        """Initialize soil service with providers."""
        self.providers = {
            "usda_nrcs": USDANRCSProvider(),
            "soilgrids": SoilGridsProvider(),
        }
        logger.info(
            "Initialized SoilService with providers: %s", list(self.providers.keys())
        )

    def enrich_location(
        self, latitude: float, longitude: float, depth_cm: str | None = "0-5cm"
    ) -> SoilResult:
        """Enrich a single location with soil data.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            depth_cm: Depth interval (e.g., "0-5cm", "5-15cm")

        Returns:
            SoilResult with best available soil data
        """
        logger.info(f"Enriching soil data for location ({latitude}, {longitude})")

        # Determine provider strategy based on location
        if self._is_us_location(latitude, longitude):
            # US locations: USDA primary, SoilGrids fallback
            provider_order = ["usda_nrcs", "soilgrids"]
        else:
            # Global locations: SoilGrids only
            provider_order = ["soilgrids"]

        last_error = None

        for provider_name in provider_order:
            provider = self.providers[provider_name]

            # Check if provider is available
            if not provider.is_available():
                logger.warning(f"Provider {provider_name} is not available")
                continue

            try:
                result = provider.get_soil_data(latitude, longitude, depth_cm)

                # Check if we got useful data
                if result.observations and result.quality_score > 0.1:
                    logger.info(
                        f"Successfully retrieved soil data from {provider_name} "
                        f"(quality: {result.quality_score:.2f})"
                    )
                    return result
                else:
                    logger.info(f"Provider {provider_name} returned no useful data")
                    last_error = f"No soil data available from {provider_name}"

            except Exception as e:
                logger.warning(f"Error with provider {provider_name}: {e}")
                last_error = str(e)
                continue

        # No providers succeeded
        logger.warning(
            f"All soil providers failed for location ({latitude}, {longitude})"
        )
        return SoilResult(
            latitude=latitude,
            longitude=longitude,
            distance_m=0.0,
            observations=[],
            quality_score=0.0,
            provider="None",
            errors=[last_error or "All soil providers failed"],
        )

    def enrich_batch(
        self, locations: list[tuple[float, float]], depth_cm: str | None = "0-5cm"
    ) -> list[SoilResult]:
        """Enrich multiple locations with soil data.

        Args:
            locations: List of (latitude, longitude) tuples
            depth_cm: Depth interval for all locations

        Returns:
            List of SoilResult objects
        """
        logger.info(f"Enriching soil data for {len(locations)} locations")

        results = []
        for i, (lat, lon) in enumerate(locations):
            try:
                result = self.enrich_location(lat, lon, depth_cm)
                results.append(result)

                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(locations)} locations")

            except Exception as e:
                logger.error(f"Error processing location ({lat}, {lon}): {e}")
                results.append(
                    SoilResult(
                        latitude=lat,
                        longitude=lon,
                        distance_m=0.0,
                        observations=[],
                        quality_score=0.0,
                        provider="Error",
                        errors=[str(e)],
                    )
                )

        logger.info(f"Completed soil enrichment for {len(locations)} locations")
        return results

    def enrich_biosample(self, sample_data: dict) -> dict:
        """Enrich a single biosample with soil data.

        Args:
            sample_data: Biosample dictionary with location information

        Returns:
            Original sample_data enhanced with soil enrichment
        """
        # Extract location from biosample
        location = self._extract_location(sample_data)
        if not location:
            logger.warning("No valid location found in biosample")
            return sample_data

        lat, lon = location

        # Extract depth if available
        depth_cm = self._extract_depth(sample_data)

        # Get soil enrichment
        soil_result = self.enrich_location(lat, lon, depth_cm)

        # Add soil data to sample based on schema type
        schema_type = self._detect_schema_type(sample_data)

        if schema_type == "nmdc":
            soil_fields = soil_result.to_nmdc_schema()
        elif schema_type == "gold":
            soil_fields = soil_result.to_gold_schema()
        else:
            # Generic enrichment
            soil_fields = self._to_generic_schema(soil_result)

        # Merge enrichment into sample
        enriched_sample = sample_data.copy()
        enriched_sample.update(soil_fields)

        return enriched_sample

    def get_provider_status(self) -> dict[str, dict]:
        """Get status of all soil providers.

        Returns:
            Dictionary mapping provider names to status information
        """
        status = {}

        for name, provider in self.providers.items():
            try:
                is_available = provider.is_available()
                status[name] = {
                    "name": provider.name,
                    "available": is_available,
                    "coverage": provider.coverage_description,
                }
            except Exception as e:
                status[name] = {
                    "name": provider.name,
                    "available": False,
                    "error": str(e),
                    "coverage": provider.coverage_description,
                }

        return status

    def _is_us_location(self, latitude: float, longitude: float) -> bool:
        """Check if location is within USDA coverage area."""
        # Continental US bounding box (approximate)
        # Includes Alaska and Hawaii
        us_bounds = [
            (24.0, -125.0, 50.0, -66.0),  # Continental US
            (60.0, -180.0, 72.0, -140.0),  # Alaska
            (18.0, -161.0, 23.0, -154.0),  # Hawaii
        ]

        for min_lat, min_lon, max_lat, max_lon in us_bounds:
            if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
                return True

        return False

    def _extract_location(self, sample_data: dict) -> tuple[float, float] | None:
        """Extract latitude/longitude from biosample data."""
        # Try various field name patterns
        lat_fields = ["lat", "latitude", "decimal_latitude", "lat_lon.lat"]
        lon_fields = ["lon", "lng", "longitude", "decimal_longitude", "lat_lon.lon"]

        lat = None
        lon = None

        # Look for latitude
        for field in lat_fields:
            if field in sample_data:
                try:
                    lat = float(sample_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        # Look for longitude
        for field in lon_fields:
            if field in sample_data:
                try:
                    lon = float(sample_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        # Check for combined lat_lon field
        if (lat is None or lon is None) and "lat_lon" in sample_data:
            lat_lon = sample_data["lat_lon"]
            if isinstance(lat_lon, dict):
                try:
                    lat_val = lat_lon.get("latitude") or lat_lon.get("lat")
                    lon_val = lat_lon.get("longitude") or lat_lon.get("lon")
                    if lat_val is not None and lon_val is not None:
                        lat = float(lat_val)
                        lon = float(lon_val)
                except (ValueError, TypeError):
                    pass

        if lat is not None and lon is not None:
            return (lat, lon)

        return None

    def _extract_depth(self, sample_data: dict) -> str | None:
        """Extract sampling depth from biosample data."""
        depth_fields = ["depth", "depth_m", "depth_cm", "collection_depth"]

        for field in depth_fields:
            if field in sample_data:
                depth_value = sample_data[field]

                # Handle numeric depths (assume meters)
                if isinstance(depth_value, int | float):
                    depth_m = float(depth_value)
                    if depth_m <= 0.05:
                        return "0-5cm"
                    elif depth_m <= 0.15:
                        return "5-15cm"
                    elif depth_m <= 0.30:
                        return "15-30cm"
                    elif depth_m <= 0.60:
                        return "30-60cm"
                    elif depth_m <= 1.00:
                        return "60-100cm"
                    else:
                        return "100-200cm"

                # Handle string depths
                elif isinstance(depth_value, str):
                    depth_str = depth_value.lower()
                    if "0-5" in depth_str or "0 to 5" in depth_str:
                        return "0-5cm"
                    elif "5-15" in depth_str or "5 to 15" in depth_str:
                        return "5-15cm"
                    # Add more depth parsing as needed

        # Default to surface layer
        return "0-5cm"

    def _detect_schema_type(self, sample_data: dict) -> str:
        """Detect the schema type of biosample data."""
        # Check for NMDC-specific fields
        nmdc_indicators = ["id", "env_medium", "ecosystem_type", "sample_link"]
        if any(field in sample_data for field in nmdc_indicators):
            return "nmdc"

        # Check for GOLD-specific fields
        gold_indicators = ["biosampleName", "ncbiTaxName", "ecosystemType", "habitat"]
        if any(field in sample_data for field in gold_indicators):
            return "gold"

        return "generic"

    def _to_generic_schema(self, soil_result: SoilResult) -> dict:
        """Convert soil result to generic enrichment format."""
        if not soil_result.observations:
            return {}

        obs = soil_result.observations[0]  # Use first observation

        enrichment: dict[str, Any] = {}

        if obs.classification_usda:
            enrichment["soil_classification_usda"] = obs.classification_usda
        if obs.classification_wrb:
            enrichment["soil_classification_wrb"] = obs.classification_wrb
        if obs.ph_h2o is not None:
            enrichment["soil_ph"] = float(obs.ph_h2o)
        if obs.texture_class:
            enrichment["soil_texture_class"] = obs.texture_class
        if obs.organic_carbon is not None:
            enrichment["soil_organic_carbon_g_kg"] = float(obs.organic_carbon)
        if obs.total_nitrogen is not None:
            enrichment["soil_total_nitrogen_g_kg"] = float(obs.total_nitrogen)

        # Add metadata
        enrichment["_soil_enrichment_provider"] = soil_result.provider
        enrichment["_soil_enrichment_quality"] = float(soil_result.quality_score)
        if soil_result.distance_m:
            enrichment["_soil_enrichment_distance_m"] = soil_result.distance_m

        return enrichment
