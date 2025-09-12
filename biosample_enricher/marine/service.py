"""
Marine enrichment service for biosample oceanographic context.

Orchestrates multiple marine data providers to deliver comprehensive marine
environmental data with quality tracking and standardized schema mapping.
"""

from datetime import date, datetime
from typing import Any

from biosample_enricher.logging_config import get_logger
from biosample_enricher.marine.models import MarineQuality, MarineResult
from biosample_enricher.marine.providers.base import MarineProviderBase
from biosample_enricher.marine.providers.esa_cci import ESACCIProvider
from biosample_enricher.marine.providers.gebco import GEBCOProvider
from biosample_enricher.marine.providers.noaa_oisst import NOAAOISSTProvider

logger = get_logger(__name__)


class MarineService:
    """
    Multi-provider marine enrichment service for biosample metadata.

    Provides comprehensive oceanographic data using multiple providers with
    quality tracking and standardized output schema for marine samples.
    """

    def __init__(self, providers: list[MarineProviderBase] | None = None):
        """
        Initialize marine service with provider chain.

        Args:
            providers: List of marine providers to use.
                      If None, uses default OISST + GEBCO + ESA CCI providers.
        """
        if providers is None:
            # Default Tier 1 providers: SST, Bathymetry, Chlorophyll
            providers = [
                NOAAOISSTProvider(),  # Sea surface temperature
                GEBCOProvider(),  # Bathymetry/water depth
                ESACCIProvider(),  # Chlorophyll-a
            ]

        self.providers = providers
        logger.info(f"Marine service initialized with {len(providers)} providers")

    def get_marine_data_for_biosample(
        self, biosample: dict[str, Any], target_schema: str = "nmdc"
    ) -> dict[str, Any]:
        """
        Get marine data for a biosample and map to target schema.

        Args:
            biosample: Biosample dictionary with location and collection date
            target_schema: Target schema format ("nmdc" or "gold")

        Returns:
            Dictionary with enrichment status, marine data, and schema mapping
        """
        logger.info(
            f"Marine enrichment requested for biosample {biosample.get('id', 'unknown')}"
        )

        # Extract location coordinates
        location = self._extract_location(biosample)
        if location is None:
            return {
                "enrichment_success": False,
                "error": "no_coordinates",
                "enrichment": {},
                "marine_data": None,
            }

        # Extract collection date
        collection_date = self._extract_collection_date(biosample)
        if collection_date is None:
            return {
                "enrichment_success": False,
                "error": "no_collection_date",
                "enrichment": {},
                "marine_data": None,
            }

        logger.info(
            f"Fetching marine data for {location['lat']}, {location['lon']} on {collection_date}"
        )

        # Get comprehensive marine data
        marine_result = self.get_comprehensive_marine_data(
            location["lat"], location["lon"], collection_date
        )

        if marine_result.overall_quality == MarineQuality.NO_DATA:
            return {
                "enrichment_success": False,
                "error": "no_marine_data_available",
                "enrichment": {},
                "marine_data": marine_result,
            }

        # Map to target schema
        schema_mapping = marine_result.get_schema_mapping(target_schema)
        coverage_metrics = marine_result.get_coverage_metrics()

        return {
            "enrichment_success": True,
            "schema_mapping": schema_mapping,
            "coverage_metrics": coverage_metrics,
            "marine_result": marine_result,
            "enrichment": schema_mapping,  # For compatibility
        }

    def get_comprehensive_marine_data(
        self, latitude: float, longitude: float, target_date: date
    ) -> MarineResult:
        """
        Get comprehensive marine data from all available providers.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date for marine data query

        Returns:
            MarineResult with combined data from all providers
        """
        logger.info(f"Collecting marine data from {len(self.providers)} providers")

        # Initialize combined result
        combined_result = MarineResult(
            location={"lat": latitude, "lon": longitude},
            collection_date=target_date.strftime("%Y-%m-%d"),
        )

        successful_providers = []
        failed_providers = []
        overall_qualities = []

        # Query each provider and merge results
        for provider in self.providers:
            try:
                logger.info(f"Querying {provider.provider_name} for marine data")

                if not provider.is_available(latitude, longitude, target_date):
                    logger.info(
                        f"{provider.provider_name} not available for this location/date"
                    )
                    failed_providers.append(provider.provider_name)
                    continue

                provider_result = provider.get_marine_data(
                    latitude, longitude, target_date
                )

                if provider_result.overall_quality != MarineQuality.NO_DATA:
                    # Merge successful provider data
                    self._merge_marine_results(combined_result, provider_result)
                    successful_providers.extend(provider_result.successful_providers)
                    overall_qualities.append(provider_result.overall_quality)
                    logger.info(
                        f"{provider.provider_name} provided marine data successfully"
                    )
                else:
                    failed_providers.extend(provider_result.failed_providers)
                    logger.warning(
                        f"{provider.provider_name} failed to provide marine data"
                    )

            except Exception as e:
                logger.error(f"Error querying {provider.provider_name}: {e}")
                failed_providers.append(provider.provider_name)

        # Set combined result metadata
        combined_result.successful_providers = list(set(successful_providers))
        combined_result.failed_providers = list(set(failed_providers))

        # Determine overall quality (best available)
        if overall_qualities:
            # Prioritize: SATELLITE_L4 > SATELLITE_L3 > STATIC_DATASET > others
            quality_priority = {
                MarineQuality.SATELLITE_L4: 4,
                MarineQuality.SATELLITE_L3: 3,
                MarineQuality.STATIC_DATASET: 2,
                MarineQuality.MODEL_REANALYSIS: 1,
                MarineQuality.CLIMATOLOGY: 0,
            }
            combined_result.overall_quality = max(
                overall_qualities, key=lambda q: quality_priority.get(q, -1)
            )
        else:
            combined_result.overall_quality = MarineQuality.NO_DATA

        logger.info(
            f"Marine data collection complete: {len(successful_providers)} successful, "
            f"{len(failed_providers)} failed providers"
        )

        return combined_result

    def _merge_marine_results(self, target: MarineResult, source: MarineResult) -> None:
        """
        Merge marine data from source into target result.

        Args:
            target: Target MarineResult to merge into
            source: Source MarineResult to merge from
        """
        # Merge each marine parameter (only if target doesn't have it)
        marine_parameters = [
            "sea_surface_temperature",
            "bathymetry",
            "chlorophyll_a",
            "salinity",
            "dissolved_oxygen",
            "ph",
            "ocean_current_u",
            "ocean_current_v",
            "significant_wave_height",
        ]

        for param in marine_parameters:
            source_value = getattr(source, param)
            target_value = getattr(target, param)

            if source_value is not None and target_value is None:
                setattr(target, param, source_value)
                logger.debug(f"Merged {param} from {source.successful_providers}")

    def _extract_location(self, biosample: dict[str, Any]) -> dict[str, float] | None:
        """
        Extract latitude/longitude from biosample.

        Args:
            biosample: Biosample dictionary

        Returns:
            Dictionary with lat/lon or None if not found
        """
        # NMDC format: lat_lon.latitude / lat_lon.longitude
        if "lat_lon" in biosample:
            lat_lon = biosample["lat_lon"]
            if (
                isinstance(lat_lon, dict)
                and "latitude" in lat_lon
                and "longitude" in lat_lon
            ):
                try:
                    lat = float(lat_lon["latitude"])
                    lon = float(lat_lon["longitude"])
                    return {"lat": lat, "lon": lon}
                except (ValueError, TypeError):
                    pass

        # GOLD format: latitude / longitude
        if "latitude" in biosample and "longitude" in biosample:
            try:
                lat = float(biosample["latitude"])
                lon = float(biosample["longitude"])
                return {"lat": lat, "lon": lon}
            except (ValueError, TypeError):
                pass

        # Alternative NMDC format: separate lat/lon fields
        if "latitude" in biosample and "longitude" in biosample:
            try:
                lat = float(biosample["latitude"])
                lon = float(biosample["longitude"])
                return {"lat": lat, "lon": lon}
            except (ValueError, TypeError):
                pass

        return None

    def _extract_collection_date(self, biosample: dict[str, Any]) -> date | None:
        """
        Extract collection date from biosample.

        Args:
            biosample: Biosample dictionary

        Returns:
            Date object or None if not found/parseable
        """
        # NMDC format: collection_date.has_raw_value
        if "collection_date" in biosample:
            collection_date = biosample["collection_date"]
            if isinstance(collection_date, dict) and "has_raw_value" in collection_date:
                date_str = collection_date["has_raw_value"]
                if isinstance(date_str, str):
                    return self._parse_date(date_str)

        # GOLD format: dateCollected
        if "dateCollected" in biosample:
            date_str = biosample["dateCollected"]
            if isinstance(date_str, str):
                return self._parse_date(date_str)

        # Direct collection_date field
        if "collection_date" in biosample and isinstance(
            biosample["collection_date"], str
        ):
            return self._parse_date(biosample["collection_date"])

        return None

    def _parse_date(self, date_str: str) -> date | None:
        """
        Parse date string into date object.

        Args:
            date_str: Date string in various formats

        Returns:
            Date object or None if unparseable
        """
        # Common date formats to try
        date_formats = [
            "%Y-%m-%d",  # 2018-07-12
            "%Y-%m-%dT%H:%M:%SZ",  # 2018-07-12T07:10:00Z
            "%Y-%m-%dT%H:%MZ",  # 2018-07-12T07:10Z
            "%Y-%m-%dT%H:%M:%S",  # 2018-07-12T07:10:00
            "%Y/%m/%d",  # 2018/07/12
            "%m/%d/%Y",  # 07/12/2018
        ]

        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.date()
            except ValueError:
                continue

        logger.warning(f"Could not parse date string: {date_str}")
        return None
