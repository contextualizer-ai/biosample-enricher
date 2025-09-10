"""Open Topo Data provider for global elevation data."""

from typing import Any

from ...http_cache import request
from ...logging_config import get_logger
from ...models import FetchResult, GeoPoint
from .base import BaseElevationProvider

logger = get_logger(__name__)


class OpenTopoDataProvider(BaseElevationProvider):
    """Provider for Open Topo Data API with multiple global datasets."""

    def __init__(
        self,
        endpoint: str = "https://api.opentopodata.org/v1",
        dataset: str = "srtm30m",
    ) -> None:
        """
        Initialize Open Topo Data provider.

        Args:
            endpoint: API endpoint URL
            dataset: Dataset to use (srtm30m, srtm90m, aster30m, eudem25m)
        """
        super().__init__(
            name="open_topo_data", endpoint=f"{endpoint}/{dataset}", api_version="v1"
        )
        self.dataset = dataset
        logger.info(f"Open Topo Data provider initialized: {dataset} dataset")

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
        Fetch elevation data from Open Topo Data API.

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
                timeout=timeout_s,
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

        return dataset_info.get(self.dataset, (30.0, "EGM96"))


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

    async def fetch(
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
        return await provider.fetch(
            lat,
            lon,
            read_from_cache=read_from_cache,
            write_to_cache=write_to_cache,
            timeout_s=timeout_s,
        )
