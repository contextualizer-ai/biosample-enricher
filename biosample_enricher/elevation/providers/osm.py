"""OpenElevation/OpenTopoData (OSM-like) provider."""

from typing import Any

from ...http_cache import request
from ...logging_config import get_logger
from ...models import FetchResult, GeoPoint
from .base import BaseElevationProvider

logger = get_logger(__name__)


class OSMElevationProvider(BaseElevationProvider):
    """Provider for OpenElevation/OpenTopoData-style APIs."""

    def __init__(
        self, endpoint: str = "https://api.open-elevation.com/api/v1/lookup"
    ) -> None:
        """
        Initialize OSM-like elevation provider.

        Args:
            endpoint: API endpoint URL (defaults to open-elevation.com)
        """
        super().__init__(name="osm_elevation", endpoint=endpoint, api_version="v1")
        logger.info(f"OSM Elevation provider initialized: {endpoint}")

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
        Fetch elevation data from OpenElevation-style API.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds

        Returns:
            Fetch result with elevation data
        """
        self._validate_coordinates(lat, lon)

        logger.debug(f"Fetching elevation from OSM API: {lat:.6f}, {lon:.6f}")

        try:
            # Prepare request data (OpenElevation uses POST with JSON)
            data = {"locations": [{"latitude": lat, "longitude": lon}]}

            # Make request using cached HTTP client
            response = request(
                "POST",
                self.endpoint,
                read_from_cache=read_from_cache,
                write_to_cache=write_to_cache,
                json=data,
                timeout=timeout_s,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            response_data = response.json()

            return self._parse_response(lat, lon, response_data)

        except Exception as e:
            logger.error(f"OSM Elevation API error: {e}")
            return FetchResult(ok=False, error=str(e), raw={})

    def _parse_response(
        self, lat: float, lon: float, data: dict[str, Any]
    ) -> FetchResult:
        """
        Parse OpenElevation-style API response.

        Args:
            lat: Requested latitude
            lon: Requested longitude
            data: API response data

        Returns:
            Parsed fetch result
        """
        try:
            # Extract results
            results = data.get("results", [])
            if not results:
                return FetchResult(
                    ok=False, error="No elevation data returned", raw=data
                )

            result = results[0]
            elevation = result.get("elevation")
            result_lat = result.get("latitude", lat)
            result_lon = result.get("longitude", lon)

            if elevation is None:
                return FetchResult(
                    ok=False, error="No elevation value in response", raw=data
                )

            # Create location point
            result_location = GeoPoint(
                lat=float(result_lat), lon=float(result_lon), precision_digits=6
            )

            logger.debug(f"OSM API returned elevation: {elevation}m")

            return FetchResult(
                ok=True,
                elevation=float(elevation),
                location=result_location,
                resolution_m=90.0,  # OpenElevation typically uses SRTM 90m data
                vertical_datum="EGM96",  # SRTM uses EGM96 geoid
                raw=data,
            )

        except Exception as e:
            logger.error(f"Error parsing OSM response: {e}")
            return FetchResult(ok=False, error=f"Response parsing error: {e}", raw=data)
