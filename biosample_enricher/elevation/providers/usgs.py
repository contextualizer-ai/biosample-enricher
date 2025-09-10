"""USGS Elevation Point Query Service provider."""

from typing import Any

from ...http_cache import request
from ...logging_config import get_logger
from ...models import FetchResult, GeoPoint
from .base import BaseElevationProvider

logger = get_logger(__name__)


class USGSElevationProvider(BaseElevationProvider):
    """Provider for USGS Elevation Point Query Service."""

    def __init__(self) -> None:
        """Initialize USGS Elevation provider."""
        super().__init__(
            name="usgs_epqs",
            endpoint="https://epqs.nationalmap.gov/v1/json",
            api_version="v1",
        )
        logger.info("USGS Elevation provider initialized")

    async def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
    ) -> FetchResult:
        """
        Fetch elevation data from USGS EPQS.

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

        logger.debug(f"Fetching elevation from USGS EPQS: {lat:.6f}, {lon:.6f}")

        try:
            # Prepare request parameters for new USGS endpoint
            params = {
                "x": lon,
                "y": lat,
                "wkid": 4326,  # WGS84 spatial reference
                "units": "Meters",
                "includeDate": "true",
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
            logger.error(f"USGS EPQS error: {e}")
            return FetchResult(ok=False, error=str(e), raw={})

    def _parse_response(
        self, lat: float, lon: float, data: dict[str, Any]
    ) -> FetchResult:
        """
        Parse USGS EPQS response.

        Args:
            lat: Requested latitude
            lon: Requested longitude
            data: API response data

        Returns:
            Parsed fetch result
        """
        try:
            # New USGS endpoint returns JSON with "value" field
            elevation = data.get("value")

            # Get location data if available
            location_data = data.get("location", {})
            result_lat = location_data.get("y", lat)
            result_lon = location_data.get("x", lon)

            # Get resolution from raster metadata if available
            resolution = data.get("resolution", 10.0)  # Default to 10m

            # Check for error conditions
            if elevation is None or "failed" in str(data).lower():
                # Look for error messages
                error_msg = "No elevation data available"
                if "failed" in str(data).lower():
                    error_msg = "No elevation data available at this location"
                elif "error" in str(data).lower():
                    error_msg = "USGS service error"

                logger.warning(f"USGS EPQS no data: {error_msg}")
                return FetchResult(ok=False, error=error_msg, raw=data)

            # Convert elevation to float and handle special values
            elevation_val = float(elevation)
            if elevation_val == -1000000:  # USGS "no data" value
                return FetchResult(
                    ok=False,
                    error="No elevation data available at this location",
                    raw=data,
                )

            # Create location point with actual returned coordinates
            result_location = GeoPoint(
                lat=float(result_lat), lon=float(result_lon), precision_digits=6
            )

            logger.debug(f"USGS EPQS returned elevation: {elevation}m")

            return FetchResult(
                ok=True,
                elevation=elevation_val,
                location=result_location,
                resolution_m=float(resolution),  # Use actual resolution from response
                vertical_datum="NAVD88",  # USGS uses NAVD88 for elevation
                raw=data,
            )

        except Exception as e:
            logger.error(f"Error parsing USGS response: {e}")
            return FetchResult(ok=False, error=f"Response parsing error: {e}", raw=data)
