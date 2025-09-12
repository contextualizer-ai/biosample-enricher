"""
NOAA OISST v2.1 provider for sea surface temperature data.

NOAA Optimum Interpolation Sea Surface Temperature provides global daily SST
on a 0.25-degree grid from 1981 to present via ERDDAP.
"""

from datetime import date
from typing import Any

import requests

from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.marine.models import (
    MarineObservation,
    MarinePrecision,
    MarineQuality,
    MarineResult,
)
from biosample_enricher.marine.providers.base import MarineProviderBase

logger = get_logger(__name__)


class NOAAOISSTProvider(MarineProviderBase):
    """NOAA OISST v2.1 sea surface temperature provider."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize NOAA OISST provider.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.base_url = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"
        self.dataset_id = "ncdc_oisst_v2_avhrr_by_time_zlev_lat_lon"

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "noaa_oisst"

    def get_provider_info(self) -> dict[str, Any]:
        """Get NOAA OISST provider information."""
        return {
            "name": self.provider_name,
            "description": "NOAA Optimum Interpolation Sea Surface Temperature v2.1",
            "spatial_resolution": "0.25 degrees",
            "temporal_resolution": "daily",
            "coverage_start": "1981-09-01",
            "coverage_end": "present",
            "parameters": ["sea_surface_temperature"],
            "units": {"sst": "Celsius"},
            "data_source": "NOAA NCEI",
            "access_method": "ERDDAP griddap",
            "authentication": False,
        }

    def get_coverage_period(self) -> dict[str, str]:
        """Get temporal coverage."""
        return {"start": "1981-09-01", "end": "present"}

    def is_available(
        self, latitude: float, longitude: float, target_date: date
    ) -> bool:
        """Check if OISST data is available for location and date.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date to check

        Returns:
            True if data should be available
        """
        if not self._validate_coordinates(latitude, longitude):
            return False

        # OISST coverage starts 1981-09-01
        start_date = date(1981, 9, 1)

        # Global ocean coverage (should be available everywhere)
        return target_date >= start_date

    def get_marine_data(
        self,
        latitude: float,
        longitude: float,
        target_date: date,
        _parameters: list[str] | None = None,
    ) -> MarineResult:
        """Get SST data from NOAA OISST.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date for SST query
            parameters: Optional parameter filter (ignored - only SST available)

        Returns:
            MarineResult with SST data
        """
        logger.info(
            f"Fetching OISST SST data for {latitude}, {longitude} on {target_date}"
        )

        # Initialize result
        result = MarineResult(
            location={"lat": latitude, "lon": longitude},
            collection_date=target_date.strftime("%Y-%m-%d"),
        )

        if not self.is_available(latitude, longitude, target_date):
            logger.warning(
                f"OISST data not available for {latitude}, {longitude} on {target_date}"
            )
            result.failed_providers = [self.provider_name]
            return result

        try:
            sst_value = self._fetch_sst_data(latitude, longitude, target_date)

            if sst_value is not None:
                precision = MarinePrecision(
                    method="satellite_interpolation",
                    target_date=target_date.strftime("%Y-%m-%d"),
                    data_quality=MarineQuality.SATELLITE_L4,
                    spatial_resolution="0.25°",
                    temporal_resolution="daily",
                    provider=self.provider_name,
                )

                result.sea_surface_temperature = MarineObservation(
                    value=sst_value,
                    unit="Celsius",
                    precision=precision,
                    quality_score=90,  # High quality for OISST L4 product
                )

                result.successful_providers = [self.provider_name]
                result.overall_quality = MarineQuality.SATELLITE_L4

                logger.info(f"Successfully retrieved SST: {sst_value}°C")
            else:
                logger.warning("OISST returned null SST value")
                result.failed_providers = [self.provider_name]

        except Exception as e:
            logger.error(f"Error fetching OISST data: {e}")
            result.failed_providers = [self.provider_name]

        return result

    def _fetch_sst_data(
        self, latitude: float, longitude: float, target_date: date
    ) -> float | None:
        """Fetch SST data from OISST ERDDAP endpoint.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date for query

        Returns:
            SST value in Celsius or None if unavailable
        """
        try:
            # Convert longitude to 0-360 if negative (OISST uses 0-360 longitude)
            lon_360 = longitude if longitude >= 0 else longitude + 360

            # Format date for ERDDAP (ISO format)
            date_str = target_date.strftime("%Y-%m-%d")

            # Build ERDDAP query URL
            url = (
                f"{self.base_url}/{self.dataset_id}.csv"
                f"?sst[({date_str}):1:({date_str})]"
                f"[(0.0):1:(0.0)]"  # Surface level (zlev=0)
                f"[({latitude}):1:({latitude})]"
                f"[({lon_360}):1:({lon_360})]"
            )

            logger.debug(f"OISST query URL: {url}")

            # Make cached request
            response = request("GET", url, timeout=self.timeout)
            response.raise_for_status()

            # Parse CSV response
            lines = response.text.strip().split("\n")

            if len(lines) < 2:
                logger.warning("OISST response has no data rows")
                return None

            # Skip header row, get data row
            data_line = lines[1]
            values = data_line.split(",")

            if len(values) < 4:
                logger.warning(f"OISST response malformed: {data_line}")
                return None

            # SST is typically the last column
            sst_str = values[-1].strip()

            if sst_str in ["NaN", "", "null"]:
                logger.warning("OISST returned NaN/null SST value")
                return None

            sst_value = float(sst_str)

            # Sanity check SST range (-5 to 50°C)
            if not -5.0 <= sst_value <= 50.0:
                logger.warning(f"OISST SST value outside expected range: {sst_value}°C")
                return None

            return sst_value

        except requests.exceptions.RequestException as e:
            logger.error(f"OISST request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"OISST data parsing failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected OISST error: {e}")
            return None
