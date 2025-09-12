"""Google Elevation API provider."""

from typing import Any

from biosample_enricher.config import get_api_key, get_provider_config
from biosample_enricher.elevation.providers.base import BaseElevationProvider
from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.models import FetchResult, GeoPoint

logger = get_logger(__name__)


class GoogleElevationProvider(BaseElevationProvider):
    """Provider for Google Elevation API."""

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize Google Elevation provider.

        Args:
            api_key: Google API key (if None, loads from configuration)
        """
        # Load provider configuration
        config = get_provider_config("elevation", "google")
        if not config:
            raise ValueError("Google elevation provider configuration not found")

        if not config.enabled:
            raise ValueError("Google elevation provider is disabled in configuration")

        super().__init__(
            name="google_elevation",
            endpoint=config.endpoint,
            api_version="v1",
        )

        # Load API key from config or parameter
        self.api_key: str | None
        if api_key:
            self.api_key = api_key
        elif config.api_key_env:
            self.api_key = get_api_key(config.api_key_env)
        else:
            self.api_key = None

        if not self.api_key:
            raise ValueError(
                f"Google API key required. Set {config.api_key_env} environment variable "
                "or pass api_key parameter."
            )

        # Store configuration for request parameters
        self.timeout_s = config.timeout_s
        self.rate_limit_qps = config.rate_limit_qps
        self.vertical_datum = config.vertical_datum or "EGM96"

        logger.info("Google Elevation provider initialized")

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float | None = None,
    ) -> FetchResult:
        """
        Fetch elevation data from Google Elevation API.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds (uses provider config default if None)

        Returns:
            Fetch result with elevation data
        """
        self._validate_coordinates(lat, lon)

        # Use configured timeout if not specified
        actual_timeout = timeout_s if timeout_s is not None else self.timeout_s

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
                timeout=actual_timeout,
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
                vertical_datum=self.vertical_datum,
                raw=data,
            )

        except Exception as e:
            logger.error(f"Error parsing Google response: {e}")
            return FetchResult(ok=False, error=f"Response parsing error: {e}", raw=data)
