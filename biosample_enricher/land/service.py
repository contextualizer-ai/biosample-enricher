"""Land cover and vegetation enrichment service orchestration."""

from datetime import date
from typing import Any

from biosample_enricher.land.models import (
    LandResult,
)
from biosample_enricher.land.providers.esa_worldcover import ESAWorldCoverProvider
from biosample_enricher.land.providers.modis_vegetation import MODISVegetationProvider
from biosample_enricher.land.providers.nlcd import NLCDProvider
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class LandService:
    """Multi-provider land cover and vegetation enrichment service.

    Queries ALL available providers for comprehensive data coverage:
    - Land Cover: ESA WorldCover, NLCD (US), MODIS Land Cover, CGLS
    - Vegetation: MODIS NDVI/EVI/LAI/FPAR, VIIRS NDVI, Sentinel-2 (selective)

    Returns full provenance with exact coordinates/dates from each provider.
    """

    def __init__(self):
        """Initialize land service with all providers."""
        # Land cover providers
        self.land_cover_providers = {
            "esa_worldcover": ESAWorldCoverProvider(),
            "nlcd": NLCDProvider(),
            # TODO: Add MODIS Land Cover, CGLS providers
        }

        # Vegetation index providers
        self.vegetation_providers = {
            "modis_vegetation": MODISVegetationProvider(),
            # TODO: Add VIIRS, Sentinel-2 providers
        }

        logger.info(
            f"Initialized LandService with {len(self.land_cover_providers)} land cover "
            f"and {len(self.vegetation_providers)} vegetation providers"
        )

    def enrich_location(
        self,
        latitude: float,
        longitude: float,
        target_date: date | None = None,
        time_window_days: int = 16,
    ) -> LandResult:
        """Enrich a single location with land cover and vegetation data.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Target date for temporal alignment
            time_window_days: Search window for vegetation indices

        Returns:
            LandResult with data from ALL available providers
        """
        logger.info(
            f"Enriching land data for location ({latitude}, {longitude}) "
            f"target_date={target_date}"
        )

        requested_location = {"lat": latitude, "lon": longitude}

        # Query ALL land cover providers
        land_cover_observations = []
        land_cover_errors = []
        providers_attempted = []
        providers_successful = []

        for provider_name, provider in self.land_cover_providers.items():
            providers_attempted.append(f"land_cover:{provider_name}")

            try:
                if not provider.is_available():
                    logger.warning(
                        f"Land cover provider {provider_name} is not available"
                    )
                    land_cover_errors.append(f"{provider_name} not available")
                    continue

                observations = provider.get_land_cover(latitude, longitude, target_date)

                if observations:
                    land_cover_observations.extend(observations)
                    providers_successful.append(f"land_cover:{provider_name}")
                    logger.info(
                        f"Retrieved {len(observations)} land cover observations from {provider_name}"
                    )
                else:
                    logger.info(f"No land cover data from {provider_name}")

            except Exception as e:
                logger.error(f"Error with land cover provider {provider_name}: {e}")
                land_cover_errors.append(f"{provider_name}: {str(e)}")

        # Query ALL vegetation providers
        vegetation_observations = []
        vegetation_errors = []

        for provider_name, provider in self.vegetation_providers.items():
            providers_attempted.append(f"vegetation:{provider_name}")

            try:
                if not provider.is_available():
                    logger.warning(
                        f"Vegetation provider {provider_name} is not available"
                    )
                    vegetation_errors.append(f"{provider_name} not available")
                    continue

                observations = provider.get_vegetation_indices(
                    latitude, longitude, target_date, time_window_days
                )

                if observations:
                    vegetation_observations.extend(observations)
                    providers_successful.append(f"vegetation:{provider_name}")
                    logger.info(
                        f"Retrieved {len(observations)} vegetation observations from {provider_name}"
                    )
                else:
                    logger.info(f"No vegetation data from {provider_name}")

            except Exception as e:
                logger.error(f"Error with vegetation provider {provider_name}: {e}")
                vegetation_errors.append(f"{provider_name}: {str(e)}")

        # Calculate overall quality score
        total_attempted = len(providers_attempted)
        total_successful = len(providers_successful)
        overall_quality = (
            total_successful / total_attempted if total_attempted > 0 else 0.0
        )

        # Combine all errors
        all_errors = land_cover_errors + vegetation_errors

        logger.info(
            f"Land enrichment complete: {total_successful}/{total_attempted} providers successful, "
            f"{len(land_cover_observations)} land cover + {len(vegetation_observations)} vegetation obs"
        )

        return LandResult(
            requested_location=requested_location,
            requested_date=target_date,
            land_cover=land_cover_observations,
            vegetation=vegetation_observations,
            overall_quality_score=overall_quality,
            providers_attempted=providers_attempted,
            providers_successful=providers_successful,
            errors=all_errors,
        )

    def enrich_batch(
        self,
        locations: list[tuple[float, float]],
        target_date: date | None = None,
        time_window_days: int = 16,
    ) -> list[LandResult]:
        """Enrich multiple locations with land cover and vegetation data.

        Args:
            locations: List of (latitude, longitude) tuples
            target_date: Target date for all locations
            time_window_days: Search window for vegetation indices

        Returns:
            List of LandResult objects
        """
        logger.info(f"Enriching land data for {len(locations)} locations")

        results = []
        for i, (lat, lon) in enumerate(locations):
            try:
                result = self.enrich_location(lat, lon, target_date, time_window_days)
                results.append(result)

                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(locations)} locations")

            except Exception as e:
                logger.error(f"Error processing location ({lat}, {lon}): {e}")
                # Create error result
                results.append(
                    LandResult(
                        requested_location={"lat": lat, "lon": lon},
                        requested_date=target_date,
                        land_cover=[],
                        vegetation=[],
                        overall_quality_score=0.0,
                        providers_attempted=[],
                        providers_successful=[],
                        errors=[str(e)],
                    )
                )

        logger.info(f"Completed land enrichment for {len(locations)} locations")
        return results

    def enrich_biosample(self, sample_data: dict[str, Any]) -> dict[str, Any]:
        """Enrich a single biosample with land cover and vegetation data.

        Args:
            sample_data: Biosample dictionary with location information

        Returns:
            Original sample_data enhanced with land enrichment
        """
        # Extract location from biosample
        location = self._extract_location(sample_data)
        if not location:
            logger.warning("No valid location found in biosample")
            return sample_data

        lat, lon = location

        # Extract date if available
        target_date = self._extract_date(sample_data)

        # Get land enrichment
        land_result = self.enrich_location(lat, lon, target_date)

        # Add land data to sample based on schema type
        schema_type = self._detect_schema_type(sample_data)

        if schema_type == "nmdc":
            land_fields = land_result.to_nmdc_schema()
        elif schema_type == "gold":
            land_fields = land_result.to_gold_schema()
        else:
            # Generic enrichment
            land_fields = self._to_generic_schema(land_result)

        # Merge enrichment into sample
        enriched_sample = sample_data.copy()
        enriched_sample.update(land_fields)

        return enriched_sample

    def get_provider_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all land cover and vegetation providers.

        Returns:
            Dictionary mapping provider names to status information
        """
        status = {}

        # Check land cover providers
        for name, provider in self.land_cover_providers.items():
            try:
                is_available = provider.is_available()
                status[f"land_cover:{name}"] = {
                    "name": provider.name,
                    "type": "land_cover",
                    "available": is_available,
                    "coverage": provider.coverage_description,
                }
            except Exception as e:
                status[f"land_cover:{name}"] = {
                    "name": provider.name,
                    "type": "land_cover",
                    "available": False,
                    "error": str(e),
                    "coverage": provider.coverage_description,
                }

        # Check vegetation providers
        for name, provider in self.vegetation_providers.items():
            try:
                is_available = provider.is_available()
                status[f"vegetation:{name}"] = {
                    "name": provider.name,
                    "type": "vegetation",
                    "available": is_available,
                    "coverage": provider.coverage_description,
                }
            except Exception as e:
                status[f"vegetation:{name}"] = {
                    "name": provider.name,
                    "type": "vegetation",
                    "available": False,
                    "error": str(e),
                    "coverage": provider.coverage_description,
                }

        return status

    def _extract_location(
        self, sample_data: dict[str, Any]
    ) -> tuple[float, float] | None:
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

    def _extract_date(self, sample_data: dict[str, Any]) -> date | None:
        """Extract sampling date from biosample data."""
        date_fields = ["collection_date", "date_collected", "sampling_date", "date"]

        for field in date_fields:
            if field in sample_data:
                try:
                    date_str = str(sample_data[field])
                    # Handle various date formats
                    from datetime import datetime

                    # Try ISO format first
                    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d"]:
                        try:
                            parsed_date = datetime.strptime(date_str[:10], fmt).date()
                            return parsed_date
                        except ValueError:
                            continue

                except (ValueError, TypeError):
                    continue

        return None

    def _detect_schema_type(self, sample_data: dict[str, Any]) -> str:
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

    def _to_generic_schema(self, land_result: LandResult) -> dict[str, Any]:
        """Convert land result to generic enrichment format."""
        enrichment: dict[str, Any] = {}

        # Add best land cover data
        if land_result.land_cover:
            # Use highest confidence land cover
            best_lc = max(land_result.land_cover, key=lambda x: x.confidence or 0.0)

            enrichment["land_cover_class"] = best_lc.class_label
            enrichment["land_cover_code"] = best_lc.class_code
            enrichment["land_cover_system"] = best_lc.classification_system
            enrichment["land_cover_provider"] = best_lc.provider

        # Add best vegetation indices
        if land_result.vegetation:
            # Use temporally closest vegetation data
            best_veg = min(
                [
                    v
                    for v in land_result.vegetation
                    if v.temporal_offset_days is not None
                ],
                key=lambda x: abs(x.temporal_offset_days or 0),
                default=land_result.vegetation[0],
            )

            if best_veg.ndvi is not None:
                enrichment["ndvi"] = float(best_veg.ndvi)
            if best_veg.evi is not None:
                enrichment["evi"] = float(best_veg.evi)
            if best_veg.lai is not None:
                enrichment["lai"] = float(best_veg.lai)
            if best_veg.fpar is not None:
                enrichment["fpar"] = float(best_veg.fpar)

            enrichment["vegetation_provider"] = best_veg.provider

        # Add metadata
        enrichment["_land_enrichment_quality"] = float(
            land_result.overall_quality_score
        )
        enrichment["_land_providers_successful"] = land_result.providers_successful

        return enrichment
