"""
Get submission-schema compliant values for NMDC biosample enrichment.

This module provides a single entry point for retrieving environmental data
formatted for NMDC submission-schema slots. It orchestrates calls to multiple
provider services and extracts specific slot values in the correct units and formats.

Supported Slots
---------------

Climate (Multi-year averages, from Meteostat 30-year normals 1991-2020):
    annual_precpt (float, mm):
        Mean annual precipitation. Average of all annual precipitation values
        or estimated equivalent from regional indexes or Isohyetal maps.
        Requires: lat, lon
        Provider: MeteostatProvider.get_climate_normals()
        Note: 30-year average, does NOT require datetime

    annual_temp (float, °C):
        Mean annual temperature averaged over 30-year period.
        Requires: lat, lon
        Provider: MeteostatProvider.get_climate_normals()
        Note: 30-year average, does NOT require datetime

Weather (Point-in-time observations, from Meteostat/Open-Meteo):
    temp (float, °C):
        Temperature at the time of sampling.
        Requires: lat, lon, datetime (collection date/time)
        Provider: WeatherService.get_daily_weather()
        Note: Ideally as close to collection time as possible

    air_temp (float, °C):
        Air temperature at the time of sampling. Same as temp for atmospheric samples.
        Requires: lat, lon, datetime (collection date/time)
        Provider: WeatherService.get_daily_weather()
        Note: Ideally as close to collection time as possible

    humidity (string, "X.X g/m3"):
        Amount of water vapor in the air at time of sampling.
        Requires: lat, lon, datetime (collection date/time)
        Provider: WeatherService.get_daily_weather()
        Note: Returns string with unit, e.g., "15.2 g/m3"

    wind_speed (string, "X.X m/s"):
        Speed of wind measured at the time of sampling.
        Requires: lat, lon, datetime (collection date/time)
        Provider: WeatherService.get_daily_weather()
        Note: Returns string with unit, e.g., "5.5 m/s"

    wind_direction (string):
        Direction from which wind originates.
        Requires: lat, lon, datetime (collection date/time)
        Provider: WeatherService.get_daily_weather()
        Note: Returns string with degrees, e.g., "245 degrees"

    solar_irradiance (string, "X.X W/m²"):
        Amount of solar energy arriving at a surface area during time interval.
        Requires: lat, lon, datetime (collection date/time)
        Provider: WeatherService.get_daily_weather()
        Note: Returns string with unit, e.g., "850.5 W/m²"

Elevation/Topography (from USGS, Open Topo Data, Google):
    elev (float, m):
        Elevation (height above mean sea level) of the sampling site in meters.
        Used for points on earth's surface (terrestrial, aquatic sampling sites).
        Requires: lat, lon
        Provider: ElevationService.get_elevation()
        Note: For ground surface elevations only. Cannot determine altitude of
              airborne samples (aircraft, balloons) from lat/lon alone.

Marine/Bathymetry (from GEBCO, ESA CCI, NOAA):
    depth (string, "X.X m"):
        Vertical distance below local surface. For marine samples, this is
        water depth (bathymetry). For terrestrial subsurface samples, this is
        soil depth and must be measured, not inferred.
        Requires: lat, lon
        Provider: MarineService.get_bathymetry()
        Note: Returns bathymetry only (ocean floor depth). Does NOT return
              soil depth or sampling depth within water column.

Soil Properties (from SoilGrids, USDA NRCS):
    ph (float):
        pH measurement of sample, liquid portion, or aqueous phase.
        Requires: lat, lon
        Provider: SoilService.get_soil_properties()
        Note: Returns surface (0-5cm) pH value

    soil_type (string):
        Description of soil type or classification (ENVO terms preferred).
        Requires: lat, lon
        Provider: SoilService.get_soil_properties()
        Example: "plinthosol [ENVO:00002250]"

Land Cover/Vegetation (from ESA WorldCover, MODIS, NLCD):
    cur_vegetation (string):
        Current vegetation classification from standard systems or agricultural crop.
        Requires: lat, lon
        Provider: LandService (future)
        Status: Placeholder - needs implementation
        Examples: "deciduous forest", "Bauhinia variegata"

Flooding (from USGS, NOAA):
    flooding (string):
        Historical and/or physical evidence of flooding with dates.
        Requires: lat, lon
        Provider: FloodingService (future - Issue #192)
        Status: Placeholder - needs research
        Format: "YYYY-MM-DD" or "YYYY-MM to YYYY-MM"

Usage Example
-------------
    >>> from datetime import datetime
    >>> from biosample_enricher.submission_values import get_submission_values
    >>>
    >>> # Get annual climate values (no datetime needed)
    >>> values = get_submission_values(
    ...     lat=37.7749,
    ...     lon=-122.4194,
    ...     slots=["annual_precpt", "annual_temp", "elev"]
    ... )
    >>> print(values)
    {
        "annual_precpt": 453.1,    # mm/year (30-year average)
        "annual_temp": 14.6,        # °C (30-year average)
        "elev": 52.0                # m above sea level
    }
    >>>
    >>> # Get day-specific weather values (datetime required)
    >>> values = get_submission_values(
    ...     lat=37.7749,
    ...     lon=-122.4194,
    ...     slots=["temp", "humidity", "wind_speed"],
    ...     datetime_obj=datetime(2023, 7, 15, 14, 30)
    ... )
    >>> print(values)
    {
        "temp": 22.3,              # °C on 2023-07-15
        "humidity": "12.5 g/m3",   # at time of sampling
        "wind_speed": "5.2 m/s"    # at time of sampling
    }
    >>>
    >>> # Mix of annual and day-specific values
    >>> values = get_submission_values(
    ...     lat=40.7128,
    ...     lon=-74.0060,
    ...     slots=["annual_precpt", "temp", "elev", "ph"],
    ...     datetime_obj=datetime(2023, 7, 15)
    ... )
    >>> print(values)
    {
        "annual_precpt": 1268.4,   # 30-year average
        "temp": 28.1,              # Day-specific temperature
        "elev": 10.0,              # Elevation
        "ph": 6.2                  # Surface soil pH
    }

Implementation Details
----------------------
This function:
1. Groups requested slots by the service they require (weather, elevation, soil, marine)
2. Makes ONE call per service to fetch all needed data efficiently
3. Extracts specific slot values in submission-schema format and units
4. Returns only successfully retrieved values (missing/failed slots are omitted)
5. Handles errors gracefully - partial success is allowed

Data Sources:
- Weather: Meteostat (station-based historical), Open-Meteo (gridded reanalysis)
- Elevation: USGS 3DEP, Open Topo Data, Google Elevation API
- Soil: SoilGrids (global 250m), USDA NRCS (US only)
- Marine: GEBCO bathymetry, ESA CCI ocean color, NOAA OISST

Units and Formats:
All values are returned in the units specified by submission-schema:
- Temperatures: degrees Celsius (float)
- Precipitation: millimeters (float)
- Distances: meters (float or string with "m")
- Wind speed: meters per second (string with "m/s")
- Humidity: grams per cubic meter (string with "g/m3")
- pH: unitless (float, 0-14 scale)

Known Limitations and Future Work:
1. **Sample Type Validation**: Currently does NOT validate whether requested slots
   are appropriate for the sample location. For example:
   - Will return soil pH/soil_type even for ocean locations
   - Will return bathymetric depth even for terrestrial locations
   - Future work needed to classify locations as: terrestrial soil, inland/freshwater,
     coastal, or open ocean, and validate slot requests accordingly.

2. **Unsupported Slots Requiring Measured Data**:
   - alt (altitude): For airborne samples (aircraft, balloons) - requires measurement
   - salinity: Requires water sample analysis or oceanographic models - not yet implemented
   - cur_vegetation: Requires land cover classification - not yet implemented
   - flooding: Requires historical flood data - not yet implemented (Issue #192)

3. **Depth Interpretation**: The 'depth' slot currently returns bathymetry (ocean floor
   depth) for marine locations. It does NOT return:
   - Soil sampling depth (must be measured by user)
   - Water column sampling depth (must be measured by user)
"""

from datetime import datetime
from typing import Any

from biosample_enricher.consensus import compute_consensus
from biosample_enricher.elevation.service import ElevationService
from biosample_enricher.logging_config import get_logger
from biosample_enricher.marine.service import MarineService
from biosample_enricher.models import ElevationRequest
from biosample_enricher.soil.service import SoilService
from biosample_enricher.weather.service import WeatherService

logger = get_logger(__name__)

__all__ = [
    "get_submission_values",
    "CLIMATE_SLOTS",
    "WEATHER_SLOTS",
    "ELEVATION_SLOTS",
    "MARINE_SLOTS",
    "SOIL_SLOTS",
    "ALL_SUPPORTED_SLOTS",
    "CLIMATE_PROVIDERS",
    "ELEVATION_PROVIDERS",
    "CONSENSUS_STRATEGIES",
]

# Available consensus strategies for combining multi-provider values
CONSENSUS_STRATEGIES = frozenset(["mean", "median", "first", "best_quality"])

# Supported submission schema slots
CLIMATE_SLOTS = frozenset(["annual_precpt", "annual_temp"])
WEATHER_SLOTS = frozenset(
    ["temp", "air_temp", "humidity", "wind_speed", "wind_direction", "solar_irradiance"]
)
ELEVATION_SLOTS = frozenset(["elev"])
MARINE_SLOTS = frozenset(["depth"])
SOIL_SLOTS = frozenset(["ph", "soil_type"])

ALL_SUPPORTED_SLOTS = (
    CLIMATE_SLOTS | WEATHER_SLOTS | ELEVATION_SLOTS | MARINE_SLOTS | SOIL_SLOTS
)

# Available providers by slot category
CLIMATE_PROVIDERS = frozenset(["meteostat", "nasa_power"])
ELEVATION_PROVIDERS = frozenset(["usgs", "google", "open_topo_data", "osm"])


def get_submission_values(
    lat: float,
    lon: float,
    slots: list[str],
    datetime_obj: datetime | None = None,
    providers: list[str] | None = None,
    strategy: str = "mean",
) -> dict[str, Any]:
    """
    Get NMDC submission-schema compliant values for specified slots.

    This method knows how to map submission-schema slot names to the appropriate
    provider services and extract values in the correct format and units.

    ALWAYS returns provider metadata for transparency - showing which providers
    contributed to each value and enabling quality checking by comparing sources.

    Args:
        lat: Latitude in decimal degrees (-90 to 90)
        lon: Longitude in decimal degrees (-180 to 180)
        slots: List of submission-schema slot names to retrieve.
               Must be from ALL_SUPPORTED_SLOTS constant.
               Supported slots are organized by category:
               - CLIMATE_SLOTS: annual_precpt, annual_temp
               - WEATHER_SLOTS: temp, air_temp, humidity, wind_speed, wind_direction, solar_irradiance
               - ELEVATION_SLOTS: elev
               - MARINE_SLOTS: depth
               - SOIL_SLOTS: ph, soil_type
               Examples: ["annual_precpt", "annual_temp", "temp", "elev"]
        datetime_obj: Optional datetime for temporal data (collection date/time).
                     Required for WEATHER_SLOTS (temp, air_temp, humidity, wind_speed, wind_direction, solar_irradiance)
                     Not used for CLIMATE_SLOTS, ELEVATION_SLOTS, MARINE_SLOTS, SOIL_SLOTS
        providers: Optional list of specific provider names to use (filters available providers).
                  For climate data (CLIMATE_SLOTS): Must be from CLIMATE_PROVIDERS ("meteostat", "nasa_power")
                  For elevation data (ELEVATION_SLOTS): Must be from ELEVATION_PROVIDERS ("usgs", "google", "open_topo_data", "osm")
                  If None, all available providers are queried.
        strategy: How to combine values from multiple providers (default: "mean"):
                 - "mean": Average across all successful providers
                 - "median": Middle value (robust to outliers)
                 - "first": Use first successful provider in priority order
                 - "best_quality": Use provider with best quality metric (e.g., closest station, highest resolution)

    Returns:
        Dict with two keys:
        - "values": Dict mapping slot names to their values in submission-schema format.
            Values are in the correct units as specified by submission-schema:
            - float: annual_precpt (mm), annual_temp (°C), temp (°C), air_temp (°C), elev (m), ph
            - string: humidity (g/m3), wind_speed (m/s), wind_direction, solar_irradiance, depth (m), soil_type
            Missing or failed slots are omitted (not included, not set to None).

        - "metadata": Dict with provider information for transparency:
            - "climate_normals": Provider details for annual_precpt/annual_temp (if requested)
              - "providers_used": List of provider names that contributed data
              - "consensus_strategy": How values were combined ("mean", "median", "first", "best_quality")
              - "provider_results": Dict of {provider_name: {annual_precpt, annual_temp, period, ...}}
              - "failed_providers": Dict of {provider_name: error_message}
            - "elevation": Provider details for elev (if requested)
              - "providers_used": List of provider names that contributed data
              - "consensus_strategy": How values were combined
              - "provider_results": Dict of {provider_name: {elevation_m, resolution_m, ...}}
              - "failed_providers": Dict of {provider_name: error_message}
            - "weather": Provider details for temp/humidity/etc. (future)
            - "marine": Provider details for depth (future)
            - "soil": Provider details for ph/soil_type (future)

    Raises:
        ValueError: If lat/lon are out of valid ranges
        ValueError: If slots list is empty
        ValueError: If an unsupported slot name is provided

    Example:
        >>> from datetime import datetime
        >>> result = get_submission_values(
        ...     lat=37.7749,
        ...     lon=-122.4194,
        ...     slots=["annual_precpt", "annual_temp"],
        ... )
        >>>
        >>> # Consensus values (averaged across providers)
        >>> print(result["values"])
        {"annual_precpt": 519.3, "annual_temp": 14.1}
        >>>
        >>> # See which providers contributed
        >>> print(result["metadata"]["climate_normals"]["providers_used"])
        ["meteostat", "nasa_power"]
        >>>
        >>> # Compare individual provider results
        >>> for provider, data in result["metadata"]["climate_normals"]["provider_results"].items():
        ...     print(f"{provider}: {data['annual_precpt']:.1f} mm/year ({data['period']})")
        meteostat: 453.1 mm/year (1991-2020)
        nasa_power: 585.5 mm/year (2001-2020)
    """
    # Validate inputs
    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
    if not slots:
        raise ValueError("slots list cannot be empty")

    # Validate slot names
    invalid_slots = set(slots) - ALL_SUPPORTED_SLOTS
    if invalid_slots:
        raise ValueError(
            f"Unsupported slot(s): {sorted(invalid_slots)}. "
            f"Supported slots: {sorted(ALL_SUPPORTED_SLOTS)}"
        )

    # Validate providers if specified
    if providers is not None:
        requesting_climate = bool(set(slots) & CLIMATE_SLOTS)
        requesting_elevation = bool(set(slots) & ELEVATION_SLOTS)

        # Build set of valid providers based on requested slots
        valid_providers: set[str] = set()
        if requesting_climate:
            valid_providers |= CLIMATE_PROVIDERS
        if requesting_elevation:
            valid_providers |= ELEVATION_PROVIDERS

        if valid_providers:
            invalid_providers = set(providers) - valid_providers
            if invalid_providers:
                raise ValueError(
                    f"Invalid provider(s): {sorted(invalid_providers)}. "
                    f"Valid providers for requested slots: {sorted(valid_providers)}"
                )

    logger.info(f"Getting submission values for {len(slots)} slots at ({lat}, {lon})")

    result = {}

    # Group slots by the service they require (use module-level constants)
    weather_slots = CLIMATE_SLOTS | WEATHER_SLOTS
    elevation_slots = ELEVATION_SLOTS
    marine_slots = MARINE_SLOTS
    soil_slots = SOIL_SLOTS
    land_slots = {"cur_vegetation"}
    flooding_slots = {"flooding"}

    requested_weather_slots = [s for s in slots if s in weather_slots]
    requested_elevation_slots = [s for s in slots if s in elevation_slots]
    requested_marine_slots = [s for s in slots if s in marine_slots]
    requested_soil_slots = [s for s in slots if s in soil_slots]
    requested_land_slots = [s for s in slots if s in land_slots]
    requested_flooding_slots = [s for s in slots if s in flooding_slots]

    # Collect metadata if requested
    all_metadata: dict[str, Any] = {}

    # Fetch weather data if needed
    if requested_weather_slots:
        try:
            weather_service = WeatherService()
            weather_values, weather_metadata = _get_weather_values(
                weather_service,
                lat,
                lon,
                requested_weather_slots,
                datetime_obj,
                providers,
            )
            result.update(weather_values)
            all_metadata.update(weather_metadata)
        except Exception as e:
            logger.error(f"Failed to get weather values: {e}")

    # Fetch elevation data if needed
    if requested_elevation_slots:
        try:
            elevation_service = ElevationService()
            elevation_values, elevation_metadata = _get_elevation_values(
                elevation_service,
                lat,
                lon,
                requested_elevation_slots,
                providers,
                strategy,
            )
            result.update(elevation_values)
            all_metadata.update(elevation_metadata)
        except Exception as e:
            logger.error(f"Failed to get elevation values: {e}")

    # Fetch marine data if needed
    if requested_marine_slots:
        try:
            marine_service = MarineService()
            marine_values = _get_marine_values(
                marine_service, lat, lon, requested_marine_slots, providers
            )
            result.update(marine_values)
        except Exception as e:
            logger.error(f"Failed to get marine values: {e}")

    # Fetch soil data if needed
    if requested_soil_slots:
        try:
            soil_service = SoilService()
            soil_values = _get_soil_values(
                soil_service, lat, lon, requested_soil_slots, providers
            )
            result.update(soil_values)
        except Exception as e:
            logger.error(f"Failed to get soil values: {e}")

    # Placeholder for land cover (not yet implemented)
    if requested_land_slots:
        logger.warning(
            f"Land cover slots {requested_land_slots} not yet implemented (Issue TBD)"
        )

    # Placeholder for flooding (not yet implemented)
    if requested_flooding_slots:
        logger.warning(
            f"Flooding slots {requested_flooding_slots} not yet implemented (Issue #192)"
        )

    logger.info(f"Successfully retrieved {len(result)}/{len(slots)} slot values")

    # Always return values with metadata for transparency
    return {"values": result, "metadata": all_metadata}


def _get_weather_values(
    service: WeatherService,
    lat: float,
    lon: float,
    slots: list[str],
    datetime_obj: datetime | None,
    providers: list[str] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Extract weather-related slot values.

    Returns:
        Tuple of (values_dict, metadata_dict) where metadata_dict contains
        provider information for transparency.
    """
    values: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    # Determine which data to fetch
    needs_climate_normals = any(s in ["annual_precpt", "annual_temp"] for s in slots)
    needs_daily_weather = any(
        s
        in [
            "temp",
            "air_temp",
            "humidity",
            "wind_speed",
            "wind_direction",
            "solar_irradiance",
        ]
        for s in slots
    )

    # Get climate normals for annual values
    if needs_climate_normals:
        try:
            # Get results from all providers (MultiProviderClimateNormals)
            normals = service.get_climate_normals(lat, lon, providers=providers)

            # Use consensus values by default (average across all successful providers)
            schema_values = normals.to_submission_schema(strategy="consensus")

            if "annual_precpt" in slots:
                annual_precip = schema_values.get("annual_precpt")
                if annual_precip is not None:
                    values["annual_precpt"] = annual_precip  # mm

            if "annual_temp" in slots:
                annual_temp = schema_values.get("annual_temp")
                if annual_temp is not None:
                    values["annual_temp"] = annual_temp  # °C

            # Build metadata about providers
            provider_results = {}
            for provider_name in normals.successful_providers:
                result = normals.get_provider_result(provider_name)
                if result:
                    provider_results[provider_name] = {
                        "annual_precpt": result.get_annual_precipitation(),
                        "annual_temp": result.get_annual_temperature(),
                        "returned_start_year": result.normals_period[0],
                        "returned_end_year": result.normals_period[1],
                        "station_distance_km": result.station_distance_km
                        if result.station_distance_km > 0
                        else None,
                    }

            metadata["climate_normals"] = {
                "providers_used": normals.successful_providers,
                "consensus_strategy": "mean",
                "requested_start_year": normals.requested_start_year,
                "requested_end_year": normals.requested_end_year,
                "provider_results": provider_results,
                "failed_providers": normals.failed_providers,
            }

        except Exception as e:
            logger.warning(f"Failed to get climate normals: {e}")

    # Get daily weather if date provided
    if needs_daily_weather:
        if not datetime_obj:
            logger.warning(
                f"datetime_obj required for slots {[s for s in slots if s in ['temp', 'air_temp', 'humidity', 'wind_speed', 'wind_direction', 'solar_irradiance']]} but not provided"
            )
        else:
            try:
                weather_result = service.get_daily_weather(
                    lat, lon, datetime_obj.date(), parameters=None
                )

                if (
                    "temp" in slots or "air_temp" in slots
                ) and weather_result.temperature:
                    temp_value = weather_result.temperature.value
                    if isinstance(temp_value, dict):
                        temp = temp_value.get("avg")
                    else:
                        temp = temp_value
                    if temp is not None:
                        if "temp" in slots:
                            values["temp"] = temp  # °C
                        if "air_temp" in slots:
                            values["air_temp"] = temp  # °C

                if "humidity" in slots and weather_result.humidity:
                    humidity_value = weather_result.humidity.value
                    if isinstance(humidity_value, dict):
                        humidity = humidity_value.get("avg")
                    else:
                        humidity = humidity_value
                    if humidity is not None:
                        # Convert % to g/m3 if needed (depends on provider)
                        values["humidity"] = f"{humidity} g/m3"  # string format

                if "wind_speed" in slots and weather_result.wind_speed:
                    wind_speed_value = weather_result.wind_speed.value
                    if isinstance(wind_speed_value, dict):
                        wind_speed = wind_speed_value.get("avg")
                    else:
                        wind_speed = wind_speed_value
                    if wind_speed is not None:
                        # Convert to m/s if in km/h
                        unit = weather_result.wind_speed.unit
                        if unit == "km/h":
                            wind_speed = wind_speed / 3.6
                        values["wind_speed"] = f"{wind_speed:.1f} m/s"  # string format

                if "wind_direction" in slots and weather_result.wind_direction:
                    wind_dir = weather_result.wind_direction.value
                    if wind_dir is not None:
                        values["wind_direction"] = (
                            f"{wind_dir} degrees"  # string format
                        )

                if "solar_irradiance" in slots and weather_result.solar_radiation:
                    solar_value = weather_result.solar_radiation.value
                    if isinstance(solar_value, dict):
                        solar = solar_value.get("daily_avg")
                    else:
                        solar = solar_value
                    if solar is not None:
                        values["solar_irradiance"] = f"{solar} W/m²"  # string format

            except Exception as e:
                logger.warning(f"Failed to get daily weather: {e}")

    return values, metadata


def _get_elevation_values(
    service: ElevationService,
    lat: float,
    lon: float,
    slots: list[str],
    providers: list[str] | None,
    strategy: str = "first",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Extract elevation-related slot values with metadata.

    Uses the shared consensus module to combine values from multiple providers.
    Default strategy is "first" (use first successful provider) for backwards
    compatibility, but "mean" is recommended for more robust results.

    Note: Only retrieves ground surface elevation (elev). Does NOT support
    altitude (alt) for airborne samples, as that cannot be determined from
    lat/lon alone and requires actual measurement from the sampling platform.

    Args:
        service: ElevationService instance
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        slots: List of requested slot names
        providers: Optional list of preferred provider names
        strategy: Consensus strategy - "mean", "median", "first", "best_quality"
                 Default is "first" for backwards compatibility

    Returns:
        Tuple of (values_dict, metadata_dict)
    """
    values: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    try:
        # Create ElevationRequest with preferred providers if specified
        elevation_providers = None
        if providers is not None:
            # Filter to only elevation-relevant providers
            elevation_providers = [p for p in providers if p in ELEVATION_PROVIDERS]

        request = ElevationRequest(
            latitude=lat,
            longitude=lon,
            preferred_providers=elevation_providers,
        )
        observations = service.get_elevation(request)

        # Collect data from all observations
        provider_results: dict[str, Any] = {}
        provider_elevations: dict[str, float | None] = {}
        quality_scores: dict[str, float] = {}  # For best_quality strategy
        failed_providers: dict[str, str] = {}

        for obs in observations:
            provider_name = obs.provider.name
            if obs.value_numeric is not None:
                provider_results[provider_name] = {
                    "elevation_m": obs.value_numeric,
                    "resolution_m": obs.spatial_resolution_m,
                    "distance_to_input_m": obs.distance_to_input_m,
                    "vertical_datum": obs.vertical_datum,
                }
                provider_elevations[provider_name] = obs.value_numeric
                # Use resolution as quality metric (lower is better)
                if obs.spatial_resolution_m is not None:
                    quality_scores[provider_name] = obs.spatial_resolution_m
            elif obs.error_message:
                failed_providers[provider_name] = obs.error_message

        # Use shared consensus module to compute final value
        consensus_result = compute_consensus(
            provider_elevations,
            strategy=strategy,
            quality_scores=quality_scores if strategy == "best_quality" else None,
            lower_is_better=True,  # Lower resolution = better
        )

        # Set value if we have one
        if "elev" in slots and consensus_result["value"] is not None:
            values["elev"] = consensus_result["value"]

        # Build metadata
        metadata["elevation"] = {
            "providers_used": consensus_result["providers_used"],
            "consensus_strategy": consensus_result["strategy"],
            "provider_results": provider_results,
            "failed_providers": failed_providers,
        }

    except Exception as e:
        logger.warning(f"Failed to get elevation: {e}")
        metadata["elevation"] = {
            "providers_used": [],
            "consensus_strategy": strategy,
            "provider_results": {},
            "failed_providers": {"error": str(e)},
        }

    return values, metadata


def _get_marine_values(
    service: MarineService,
    lat: float,
    lon: float,
    slots: list[str],
    _providers: list[str] | None,
) -> dict[str, Any]:
    """
    Extract marine-related slot values.

    Note: Currently only retrieves bathymetry (depth). Uses a fixed date for
    the query since bathymetry data doesn't vary temporally.
    """
    values: dict[str, Any] = {}

    try:
        from datetime import date

        # Use current date for bathymetry query (bathymetry doesn't vary temporally)
        marine_result = service.get_comprehensive_marine_data(lat, lon, date.today())

        if "depth" in slots and marine_result.bathymetry is not None:
            # bathymetry is a MarineObservation with a value
            depth_value = marine_result.bathymetry.value
            if depth_value is not None:
                # Handle both float and dict values
                if isinstance(depth_value, dict):
                    # Use first available value from dict
                    depth = next(
                        (v for v in depth_value.values() if v is not None), None
                    )
                else:
                    depth = depth_value

                if depth is not None:
                    # submission-schema expects string with unit
                    # Use absolute value since bathymetry is typically negative
                    values["depth"] = f"{abs(depth)} m"

    except Exception as e:
        logger.warning(f"Failed to get marine data: {e}")

    return values


def _get_soil_values(
    service: SoilService,
    lat: float,
    lon: float,
    slots: list[str],
    _providers: list[str] | None,
) -> dict[str, Any]:
    """
    Extract soil-related slot values.

    Note: Uses surface soil depth (0-5cm) by default for pH and classification.
    """
    values: dict[str, Any] = {}

    try:
        # Get surface soil data (0-5cm depth)
        soil_result = service.enrich_location(lat, lon, depth_cm="0-5cm")

        # SoilResult contains a list of observations - use first one with data
        if soil_result.observations:
            surface_obs = soil_result.observations[0]

            # Extract pH if available
            if "ph" in slots and surface_obs.ph_h2o is not None:
                values["ph"] = surface_obs.ph_h2o

            # Extract soil classification if available
            if "soil_type" in slots:
                # Prefer USDA classification, fallback to WRB
                if surface_obs.classification_usda:
                    values["soil_type"] = surface_obs.classification_usda
                elif surface_obs.classification_wrb:
                    values["soil_type"] = surface_obs.classification_wrb

    except Exception as e:
        logger.warning(f"Failed to get soil data: {e}")

    return values
