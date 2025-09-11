"""Google Elevation API provider."""

import os
from typing import Any

from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.models import FetchResult, GeoPoint
from biosample_enricher.elevation.providers.base import BaseElevationProvider

logger = get_logger(__name__)


class GoogleElevationProvider(BaseElevationProvider):
    """Provider for Google Elevation API."""

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize Google Elevation provider.

        Args:
            api_key: Google API key (if None, reads from GOOGLE_MAIN_API_KEY env var)
        """
        super().__init__(
            name="google_elevation",
            endpoint="https://maps.googleapis.com/maps/api/elevation/json",
            api_version="v1",
        )

        self.api_key = api_key or os.getenv("GOOGLE_MAIN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_MAIN_API_KEY environment variable "
                "or pass api_key parameter."
            )

        logger.info("Google Elevation provider initialized")

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
        Fetch elevation data from Google Elevation API.

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

        logger.debug(f"Fetching elevation from Google API: {lat:.6f}, {lon:.6f}")

        try:
            # Prepare request parameters
            params = {"locations": f"{lat},{lon}", "key": self.api_key}

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
            logger.error(f"Google Elevation API error: {e}")
            return FetchResult(ok=False, error=str(e), raw={})

    def _parse_response(
        self, lat: float, lon: float, data: dict[str, Any]
    ) -> FetchResult:
        """
        Parse Google Elevation API response.

        Args:
            lat: Requested latitude
            lon: Requested longitude
            data: API response data

        Returns:
            Parsed fetch result
        """
        try:
            # Check API status
            status = data.get("status")
            if status != "OK":
                error_msg = data.get("error_message", f"API returned status: {status}")
                logger.warning(f"Google API error: {error_msg}")
                return FetchResult(ok=False, error=error_msg, raw=data)

            # Extract results
            results = data.get("results", [])
            if not results:
                return FetchResult(
                    ok=False, error="No elevation data returned", raw=data
                )

            result = results[0]
            elevation = result.get("elevation")
            resolution = result.get("resolution")
            location = result.get("location", {})

            if elevation is None:
                return FetchResult(
                    ok=False, error="No elevation value in response", raw=data
                )

            # Create location point
            result_lat = location.get("lat", lat)
            result_lon = location.get("lng", lon)
            result_location = GeoPoint(
                lat=result_lat, lon=result_lon, precision_digits=6
            )

            logger.debug(
                f"Google API returned elevation: {elevation}m, resolution: {resolution}m"
            )

            return FetchResult(
                ok=True,
                elevation=float(elevation),
                location=result_location,
                resolution_m=float(resolution) if resolution is not None else None,
                vertical_datum="EGM96",  # Google uses EGM96 geoid
                raw=data,
            )

        except Exception as e:
            logger.error(f"Error parsing Google response: {e}")
            return FetchResult(ok=False, error=f"Response parsing error: {e}", raw=data)
