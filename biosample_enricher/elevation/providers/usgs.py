"""USGS Elevation Point Query Service provider."""

import json
from typing import Any

from biosample_enricher.elevation.providers.base import BaseElevationProvider
from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.models import FetchResult, GeoPoint

logger = get_logger(__name__)


class USGSElevationProvider(BaseElevationProvider):
    """Provider for USGS 3DEP Elevation Service.

    Note: USGS elevation services have experienced multiple migrations and can be
    unreliable. This provider has been updated from the deprecated EPQS endpoint
    to the 3DEP ArcGIS REST service. Service availability may vary.
    """

    def __init__(self) -> None:
        """Initialize USGS Elevation provider."""
        super().__init__(
            name="usgs_3dep",
            endpoint="https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/getSamples",
            api_version="arcgis",
        )
        logger.info("USGS Elevation provider initialized (3DEP ArcGIS service)")

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
    ) -> FetchResult:
        """
        Fetch elevation data from USGS 3DEP ArcGIS service.

        Note: The USGS elevation services can be unreliable. The service has migrated
        from EPQS to the 3DEP ArcGIS REST service. The endpoint may change or
        experience outages.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache (handled by http_cache)
            write_to_cache: Whether to write to cache (handled by http_cache)
            timeout_s: Request timeout in seconds

        Returns:
            Fetch result with elevation data
        """
        self._validate_coordinates(lat, lon)

        logger.debug(f"Fetching elevation from USGS 3DEP: {lat:.6f}, {lon:.6f}")

        try:
            # Prepare request parameters for ArcGIS REST API format
            # Based on working format: geometry={"x":lon,"y":lat,"spatialReference":{"wkid":4326}}
            params = {
                "geometry": json.dumps(
                    {"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}
                ),
                "geometryType": "esriGeometryPoint",
                "returnFirstValueOnly": "true",
                "f": "json",
            }

            # Make request using cached HTTP client
            response = request(
                "GET",
                self.endpoint,
                read_from_cache=read_from_cache,
                write_to_cache=write_to_cache,
                params=params,
                timeout=timeout_s,
            )

            response.raise_for_status()
            data = response.json()

            return self._parse_response(lat, lon, data)

        except Exception as e:
            logger.error(f"USGS 3DEP error: {e}")
            return FetchResult(ok=False, error=str(e), raw={})

    def _parse_response(
        self, lat: float, lon: float, data: dict[str, Any]
    ) -> FetchResult:
        """
        Parse USGS 3DEP ArcGIS response.

        Expected response format:
        {
            "samples": [
                {
                    "location": {"x": lon, "y": lat, "spatialReference": {"wkid": 4326}},
                    "locationId": 0,
                    "value": "elevation_value",
                    "rasterId": raster_id,
                    "resolution": resolution_meters
                }
            ]
        }

        Args:
            lat: Requested latitude
            lon: Requested longitude
            data: API response data

        Returns:
            Parsed fetch result
        """
        try:
            # Check for error response
            if "error" in data:
                error_info = data.get("error", {})
                error_msg = error_info.get("message", "USGS service error")
                logger.warning(f"USGS 3DEP error response: {error_msg}")
                return FetchResult(ok=False, error=error_msg, raw=data)

            # Parse samples array from ArcGIS response
            samples = data.get("samples", [])
            if not samples:
                logger.warning("USGS 3DEP returned no samples")
                return FetchResult(
                    ok=False,
                    error="No elevation data available at this location",
                    raw=data,
                )

            # Get first sample (we requested returnFirstValueOnly=true)
            sample = samples[0]
            elevation_str = sample.get("value")

            # Check for NoData value
            if elevation_str == "NoData" or elevation_str is None:
                return FetchResult(
                    ok=False,
                    error="No elevation data available at this location",
                    raw=data,
                )

            # Parse elevation value
            elevation_val = float(elevation_str)

            # Check for USGS "no data" sentinel values
            if elevation_val == -1000000 or elevation_val == -9999:
                return FetchResult(
                    ok=False,
                    error="No elevation data available at this location",
                    raw=data,
                )

            # Get location from response (may differ slightly from request)
            location_data = sample.get("location", {})
            result_lat = location_data.get("y", lat)
            result_lon = location_data.get("x", lon)

            # Create location point with actual returned coordinates
            result_location = GeoPoint(
                lat=float(result_lat), lon=float(result_lon), precision_digits=6
            )

            # Get resolution if available (typically in meters)
            resolution = sample.get("resolution", 10.0)  # Default to 10m for 3DEP

            logger.debug(f"USGS 3DEP returned elevation: {elevation_val}m")

            return FetchResult(
                ok=True,
                elevation=elevation_val,
                location=result_location,
                resolution_m=float(resolution),
                vertical_datum="NAVD88",  # USGS 3DEP uses NAVD88
                raw=data,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing USGS response: {e}")
            return FetchResult(ok=False, error=f"Response parsing error: {e}", raw=data)
