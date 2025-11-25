"""
Weather enrichment service for biosample environmental context.

Orchestrates multiple weather providers to deliver day-specific weather data
with temporal precision tracking and standardized schema mapping.
"""

from datetime import date, datetime
from typing import Any, Protocol

from biosample_enricher.logging_config import get_logger
from biosample_enricher.weather.models import (
    ClimateNormalsResult,
    MultiProviderClimateNormals,
    TemporalQuality,
    WeatherResult,
)
from biosample_enricher.weather.providers.base import WeatherProviderBase
from biosample_enricher.weather.providers.meteostat import MeteostatProvider
from biosample_enricher.weather.providers.open_meteo import OpenMeteoProvider

logger = get_logger(__name__)


class ClimateNormalsProvider(Protocol):
    """Protocol for providers that support climate normals."""

    def get_climate_normals(
        self, lat: float, lon: float, start_year: int, end_year: int
    ) -> ClimateNormalsResult: ...


class WeatherService:
    """
    Multi-provider weather enrichment service for biosample metadata.

    Provides day-specific weather data using a provider fallback chain with
    temporal precision tracking and standardized output schema.
    """

    def __init__(self, providers: list[WeatherProviderBase] | None = None):
        """
        Initialize weather service with provider chain.

        Args:
            providers: List of weather providers in priority order.
                      If None, uses default Open-Meteo + MeteoStat providers.
        """
        if providers is None:
            # Default to Open-Meteo (primary) + MeteoStat (fallback)
            providers = [OpenMeteoProvider(), MeteostatProvider()]

        self.providers = providers
        logger.info(f"Weather service initialized with {len(providers)} providers")

    def get_weather_for_biosample(
        self, biosample: dict[str, Any], target_schema: str = "nmdc"
    ) -> dict[str, Any]:
        """
        Get weather data for a biosample and map to target schema.

        Args:
            biosample: Biosample dictionary with location and collection date
            target_schema: "nmdc" or "gold" for schema mapping

        Returns:
            Dict with weather enrichment results and schema-mapped fields
        """
        # Extract location and date from biosample
        location = self._extract_location(biosample)
        collection_date = self._extract_collection_date(biosample)

        if not location:
            logger.warning("No valid coordinates found in biosample")
            return {"error": "no_coordinates", "enrichment": {}}

        if not collection_date:
            logger.warning("No valid collection date found in biosample")
            return {"error": "no_collection_date", "enrichment": {}}

        # Get weather data
        weather_result = self.get_daily_weather(
            lat=location["lat"], lon=location["lon"], target_date=collection_date
        )

        # Map to target schema
        schema_mapping = weather_result.get_schema_mapping(target_schema)

        # Generate coverage metrics
        coverage_metrics = weather_result.get_coverage_metrics()

        return {
            "weather_result": weather_result,
            "schema_mapping": schema_mapping,
            "coverage_metrics": coverage_metrics,
            "enrichment_success": len(weather_result.successful_providers) > 0,
        }

    def get_daily_weather(
        self,
        lat: float,
        lon: float,
        target_date: date,
        parameters: list[str] | None = None,
    ) -> WeatherResult:
        """
        Get daily weather data by integrating results from all providers.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            target_date: Date for weather lookup
            parameters: Optional list of specific parameters to fetch

        Returns:
            WeatherResult with integrated data from all available providers
        """
        logger.info(
            f"Getting weather for ({lat}, {lon}) on {target_date} from all providers"
        )

        all_providers_attempted = []
        all_successful_providers = []
        all_failed_providers = []
        provider_results = []

        # Query ALL providers simultaneously
        for provider in self.providers:
            provider_name = provider.provider_name
            all_providers_attempted.append(provider_name)

            try:
                # Check if provider has data available
                if not provider.is_available(lat, lon, target_date):
                    logger.info(
                        f"Provider {provider_name} not available for {target_date}"
                    )
                    all_failed_providers.append(provider_name)
                    continue

                # Fetch weather data
                result = provider.get_daily_weather(lat, lon, target_date, parameters)

                if result.successful_providers:
                    logger.info(f"Provider {provider_name} successful")
                    all_successful_providers.extend(result.successful_providers)
                    provider_results.append(result)
                else:
                    logger.warning(f"Provider {provider_name} failed")
                    all_failed_providers.extend(result.failed_providers)

            except Exception as e:
                logger.error(f"Provider {provider_name} error: {e}")
                all_failed_providers.append(provider_name)

        # Integrate data from all successful providers
        if provider_results:
            integrated_result = self._integrate_provider_results(
                provider_results, lat, lon, target_date
            )
            integrated_result.providers_attempted = all_providers_attempted
            integrated_result.successful_providers = list(set(all_successful_providers))
            integrated_result.failed_providers = list(set(all_failed_providers))
            return integrated_result
        else:
            # Create empty result if all providers failed
            return self._create_empty_result(
                lat, lon, target_date, all_providers_attempted, all_failed_providers
            )

    def get_climate_normals(
        self,
        lat: float,
        lon: float,
        years_back: int = 30,
        providers: list[str] | None = None,
    ) -> MultiProviderClimateNormals:
        """
        Get climate averages (normals) for a location from all available providers.

        By default, queries ALL available providers and returns results from each
        successful provider in a MultiProviderClimateNormals object. This allows:
        - Comparing values across different data sources
        - Detecting provider outages/failures
        - Validating data quality by cross-checking
        - Computing consensus values across providers

        Supported providers:
        - Meteostat: Station-based 1991-2020 normals (30-year WMO standard)
        - NASA POWER: Satellite-based 2001-2020 climatologies (20-year MERRA-2)

        Climate normals represent typical conditions over a multi-year period,
        providing context for biosample environmental metadata like
        annual precipitation totals and average temperatures.

        For biosample enrichment:
        - Use this for annual_precpt, annual_temp slots
        - Use get_daily_weather() for collection-date weather

        Following general-purpose design (Issue #199): This method provides
        comprehensive climate data that ANY project can use. Use the
        `to_submission_schema()` method on the result to extract values
        in submission-schema format (Issue #193).

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            years_back: Number of years back from current year to request (default: 30).
                       For example, if current year is 2025 and years_back=30,
                       requests period 1995-2025. Providers will return whatever
                       period they actually have available, which may differ.
            providers: Optional list of provider names to query (e.g., ["meteostat", "nasa_power"]).
                      If None, queries ALL available providers (default behavior).

        Returns:
            MultiProviderClimateNormals with results from all successful providers.
            The result includes both requested period and actual returned periods
            from each provider for transparency.

        Raises:
            ValueError: If no climate data available from any provider.

        Example:
            >>> service = WeatherService()
            >>> # Request 30 years back from current year (dynamic period)
            >>> normals = service.get_climate_normals(40.7128, -74.0060)
            >>>
            >>> # Get results from all successful providers
            >>> print(f"Successful providers: {normals.successful_providers}")
            Successful providers: ['meteostat', 'nasa_power']
            >>>
            >>> # Extract consensus values for submission-schema (Issue #191)
            >>> schema_values = normals.to_submission_schema(strategy="consensus")
            >>> print(f"annual_precpt: {schema_values['annual_precpt']} mm")
            annual_precpt: 907.8 mm
            >>>
            >>> # Or get result from specific provider
            >>> meteostat_result = normals.get_provider_result("meteostat")
            >>> if meteostat_result:
            >>>     print(f"Meteostat: {meteostat_result.get_annual_precipitation()} mm/year")
            Meteostat: 1268.4 mm/year
            >>>
            >>> # Query only specific providers or different period
            >>> normals = service.get_climate_normals(40.7128, -74.0060,
            ...                                       years_back=20, providers=["nasa_power"])
        """
        # Compute requested period dynamically based on current year
        end_year = datetime.now().year
        start_year = end_year - years_back

        logger.info(
            f"Getting climate normals for ({lat}, {lon}) period {start_year}-{end_year} "
            f"(years_back={years_back})"
        )

        # Import NASA POWER provider
        from biosample_enricher.weather.providers.nasa_power import NASAPowerProvider

        # Determine which providers to try
        available_providers: dict[str, type[ClimateNormalsProvider]] = {
            "meteostat": MeteostatProvider,
            "nasa_power": NASAPowerProvider,
        }

        # Default: query ALL available providers, or use user-specified
        provider_names = ["meteostat", "nasa_power"] if providers is None else providers

        # Query ALL providers and collect results
        results: dict[str, ClimateNormalsResult] = {}
        failed: dict[str, str] = {}

        for provider_name in provider_names:
            provider_class = available_providers.get(provider_name.lower())
            if not provider_class:
                logger.warning(f"Unknown provider: {provider_name}")
                failed[provider_name] = "Unknown provider"
                continue

            try:
                logger.info(f"Querying {provider_name} for climate normals")
                provider = provider_class()
                result = provider.get_climate_normals(lat, lon, start_year, end_year)

                logger.info(
                    f"Successfully retrieved climate normals from {provider_name}"
                )
                results[provider_name] = result

            except Exception as e:
                error_msg = f"{e}"
                logger.warning(f"{provider_name} failed: {error_msg}")
                failed[provider_name] = error_msg
                continue

        # Check if we got any results
        if not results:
            error_summary = "; ".join([f"{k}: {v}" for k, v in failed.items()])
            raise ValueError(
                f"No climate data available from any provider. Tried: {provider_names}. "
                f"Errors: {error_summary}"
            )

        # Return multi-provider results with requested period
        return MultiProviderClimateNormals(
            providers=results,
            location={"lat": lat, "lon": lon},
            requested_providers=provider_names,
            successful_providers=list(results.keys()),
            failed_providers=failed,
            requested_start_year=start_year,
            requested_end_year=end_year,
        )

    def _extract_location(self, biosample: dict[str, Any]) -> dict[str, float] | None:
        """Extract latitude and longitude from biosample."""

        # Try NMDC format first
        if "lat_lon" in biosample:
            lat_lon = biosample["lat_lon"]
            if isinstance(lat_lon, dict):
                lat = lat_lon.get("latitude")
                lon = lat_lon.get("longitude")
                if lat is not None and lon is not None:
                    return {"lat": float(lat), "lon": float(lon)}

        # Try GOLD format
        if "latitude" in biosample and "longitude" in biosample:
            lat = biosample["latitude"]
            lon = biosample["longitude"]
            if lat is not None and lon is not None:
                return {"lat": float(lat), "lon": float(lon)}

        # Try direct elev coordinate extraction
        if "elev" in biosample:
            # Sometimes coordinates are stored with elevation
            pass  # Would need more complex parsing

        return None

    def _extract_collection_date(self, biosample: dict[str, Any]) -> date | None:
        """Extract collection date from biosample."""

        # Try NMDC format
        if "collection_date" in biosample:
            date_info = biosample["collection_date"]
            if isinstance(date_info, dict):
                date_str = date_info.get("has_raw_value")
            else:
                date_str = date_info

            if date_str:
                return self._parse_date_string(date_str)

        # Try GOLD format
        if "dateCollected" in biosample:
            date_str = biosample["dateCollected"]
            if date_str:
                return self._parse_date_string(date_str)

        return None

    def _parse_date_string(self, date_str: str) -> date | None:
        """Parse various date string formats to date object."""
        try:
            # Handle ISO datetime strings
            if "T" in date_str:
                date_str = date_str.split("T")[0]

            # Handle YYYY-MM-DD format
            return datetime.strptime(date_str, "%Y-%m-%d").date()

        except ValueError:
            try:
                # Handle other formats
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Could not parse date string: {date_str}")
                return None

    def _integrate_provider_results(
        self,
        provider_results: list[WeatherResult],
        lat: float,
        lon: float,
        target_date: date,
    ) -> WeatherResult:
        """
        Integrate weather data from multiple providers for comprehensive coverage.

        Prioritizes higher quality data but combines all available measurements.
        """
        from biosample_enricher.weather.models import TemporalQuality, WeatherResult

        # Initialize integrated result
        integrated = WeatherResult(
            location={"lat": lat, "lon": lon},
            collection_date=target_date.strftime("%Y-%m-%d"),
            overall_quality=TemporalQuality.NO_DATA,
        )

        # For each weather parameter, select best observation from all providers
        weather_fields = [
            "temperature",
            "wind_speed",
            "wind_direction",
            "humidity",
            "solar_radiation",
            "precipitation",
            "pressure",
        ]

        best_quality = TemporalQuality.NO_DATA

        for field in weather_fields:
            best_obs = None
            best_obs_quality = TemporalQuality.NO_DATA

            # Compare observations across all providers for this field
            for result in provider_results:
                obs = getattr(result, field, None)
                if obs is not None:
                    obs_quality = obs.temporal_precision.data_quality

                    # Select observation with best temporal quality
                    if self._is_better_quality(obs_quality, best_obs_quality):
                        best_obs = obs
                        best_obs_quality = obs_quality

            # Set the best observation for this field
            if best_obs:
                setattr(integrated, field, best_obs)
                if self._is_better_quality(best_obs_quality, best_quality):
                    best_quality = best_obs_quality

        integrated.overall_quality = best_quality
        return integrated

    def _is_better_quality(
        self, new_quality: TemporalQuality, current_quality: TemporalQuality
    ) -> bool:
        """Compare temporal quality levels."""
        quality_order = [
            TemporalQuality.DAY_SPECIFIC_COMPLETE,
            TemporalQuality.DAY_SPECIFIC_PARTIAL,
            TemporalQuality.WEEKLY_COMPOSITE,
            TemporalQuality.MONTHLY_CLIMATOLOGY,
            TemporalQuality.NO_DATA,
        ]

        new_rank = quality_order.index(new_quality)
        current_rank = quality_order.index(current_quality)
        return new_rank < current_rank

    def _create_empty_result(
        self,
        lat: float,
        lon: float,
        target_date: date,
        attempted_providers: list[str],
        failed_providers: list[str],
    ) -> WeatherResult:
        """Create empty result when all providers fail."""
        return WeatherResult(
            location={"lat": lat, "lon": lon},
            collection_date=target_date.strftime("%Y-%m-%d"),
            providers_attempted=attempted_providers,
            successful_providers=[],
            failed_providers=failed_providers,
            overall_quality=TemporalQuality.NO_DATA,
        )

    def get_provider_info(self) -> list[dict[str, Any]]:
        """Get information about all configured providers."""
        return [provider.get_provider_info() for provider in self.providers]
