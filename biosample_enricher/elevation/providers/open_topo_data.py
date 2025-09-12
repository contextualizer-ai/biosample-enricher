"""Open Topo Data provider for global elevation data."""

from typing import Any

from biosample_enricher.config import get_provider_config
from biosample_enricher.elevation.providers.base import BaseElevationProvider
from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.models import FetchResult, GeoPoint

logger = get_logger(__name__)


class OpenTopoDataProvider(BaseElevationProvider):
    """Provider for Open Topo Data API with multiple global datasets."""

    def __init__(
        self,
        endpoint: str | None = None,
        dataset: str | None = None,
    ) -> None:
        """
        Initialize Open Topo Data provider.

        Args:
            endpoint: API endpoint URL (loads from configuration if None)
            dataset: Dataset to use (loads from configuration if None)
        """
        # Load provider configuration
        config = get_provider_config("elevation", "open_topo_data")
        if not config:
            raise ValueError(
                "Open Topo Data elevation provider configuration not found"
            )

        if not config.enabled:
            raise ValueError(
                "Open Topo Data elevation provider is disabled in configuration"
            )

        # Use provided values or load from config
        endpoint_url = endpoint or config.endpoint
        self.dataset = dataset or str(getattr(config, "dataset", "srtm30m"))

        # Build full endpoint with dataset
        full_endpoint = (
            f"{endpoint_url}/{self.dataset}"
            if not endpoint_url.endswith(f"/{self.dataset}")
            else endpoint_url
        )

        super().__init__(
            name="open_topo_data", endpoint=full_endpoint, api_version="v1"
        )

        # Store configuration for request parameters
        self.timeout_s = config.timeout_s
        self.rate_limit_qps = config.rate_limit_qps
        self.max_batch_size = config.max_batch_size
        self.vertical_datum = config.vertical_datum or "EGM96"
        self.default_resolution_m = config.default_resolution_m

        logger.info(f"Open Topo Data provider initialized: {self.dataset} dataset")

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
        Fetch elevation data from Open Topo Data API.

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

        logger.debug(
            f"Fetching elevation from Open Topo Data ({self.dataset}): {lat:.6f}, {lon:.6f}"
        )

        try:
            # Prepare request parameters
            params = {"locations": f"{lat},{lon}"}

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
            logger.error(f"Open Topo Data API error: {e}")
            return FetchResult(ok=False, error=str(e), raw={})

    def _parse_response(
        self, lat: float, lon: float, data: dict[str, Any]
    ) -> FetchResult:
        """
        Parse Open Topo Data API response.

        Args:
            lat: Requested latitude
            lon: Requested longitude
            data: API response data

        Returns:
            Parsed fetch result
        """
        try:
            # Check for API errors
            status = data.get("status")
            if status != "OK":
                error_msg = data.get("error", "Unknown API error")
                return FetchResult(ok=False, error=f"API error: {error_msg}", raw=data)

            # Extract results
            results = data.get("results", [])
            if not results:
                return FetchResult(
                    ok=False, error="No elevation data returned", raw=data
                )

            result = results[0]
            elevation = result.get("elevation")
            result_lat = result.get("location", {}).get("lat", lat)
            result_lon = result.get("location", {}).get("lng", lon)

            if elevation is None:
                return FetchResult(
                    ok=False, error="No elevation value in response", raw=data
                )

            # Create location point
            result_location = GeoPoint(
                lat=float(result_lat), lon=float(result_lon), precision_digits=6
            )

            # Determine resolution and datum based on dataset
            resolution_m, vertical_datum = self._get_dataset_metadata()

            logger.debug(
                f"Open Topo Data ({self.dataset}) returned elevation: {elevation}m"
            )

            return FetchResult(
                ok=True,
                elevation=float(elevation),
                location=result_location,
                resolution_m=resolution_m,
                vertical_datum=vertical_datum,
                raw=data,
            )

        except Exception as e:
            logger.error(f"Error parsing Open Topo Data response: {e}")
            return FetchResult(ok=False, error=f"Response parsing error: {e}", raw=data)

    def _get_dataset_metadata(self) -> tuple[float, str]:
        """Get resolution and vertical datum for the current dataset."""
        dataset_info = {
            "srtm30m": (30.0, "EGM96"),
            "srtm90m": (90.0, "EGM96"),
            "aster30m": (30.0, "EGM96"),
            "eudem25m": (25.0, "EVRS2000"),  # European Vertical Reference System
            "mapzen": (30.0, "EGM96"),  # Mixed sources
            "ned10m": (10.0, "NAVD88"),  # US only
        }

        default_resolution, default_datum = dataset_info.get(
            self.dataset, (30.0, "EGM96")
        )
        # Use configured values if available, otherwise fall back to dataset defaults
        resolution = self.default_resolution_m or default_resolution
        datum = self.vertical_datum
        return (resolution, datum)


class SmartOpenTopoDataProvider(BaseElevationProvider):
    """Smart Open Topo Data provider that selects optimal dataset by location."""

    def __init__(self, endpoint: str = "https://api.opentopodata.org/v1") -> None:
        """Initialize smart provider with automatic dataset selection."""
        super().__init__(
            name="open_topo_data_smart", endpoint=endpoint, api_version="v1"
        )
        self.endpoint_base = endpoint
        logger.info("Smart Open Topo Data provider initialized")

    def _select_dataset(self, lat: float, lon: float) -> str:
        """Select optimal dataset based on coordinate location."""

        # European Union DEM for Europe
        if 35 <= lat <= 65 and -15 <= lon <= 40:
            return "eudem25m"

        # For polar regions outside SRTM coverage, use ASTER
        if lat > 60 or lat < -60:
            return "aster30m"

        # Default to SRTM 30m for best global coverage
        return "srtm30m"

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
    ) -> FetchResult:
        """Fetch elevation using optimal dataset for location."""

        # Select best dataset for this location
        dataset = self._select_dataset(lat, lon)

        # Create provider for selected dataset
        provider = OpenTopoDataProvider(endpoint=self.endpoint_base, dataset=dataset)

        # Delegate to specific provider
        return provider.fetch(
            lat,
            lon,
            read_from_cache=read_from_cache,
            write_to_cache=write_to_cache,
            timeout_s=timeout_s,
        )
