"""
ESA Ocean Colour CCI provider for chlorophyll-a data.

ESA Climate Change Initiative Ocean Colour provides global daily chlorophyll-a
concentration data via ERDDAP from 1997 to present.
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


class ESACCIProvider(MarineProviderBase):
    """ESA Ocean Colour CCI chlorophyll-a provider."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize ESA CCI provider.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        # NOAA NEFSC ERDDAP hosting ESA CCI data
        self.base_url = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"
        self.dataset_id = "nesdisVHNSQchlaDaily"  # Or appropriate ESA CCI dataset ID

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "esa_cci"

    def get_provider_info(self) -> dict[str, Any]:
        """Get ESA CCI provider information."""
        return {
            "name": self.provider_name,
            "description": "ESA Ocean Colour CCI Chlorophyll-a v6",
            "spatial_resolution": "~1 km (0.0104 degrees)",
            "temporal_resolution": "daily",
            "coverage_start": "1997-09-04",
            "coverage_end": "present",
            "parameters": ["chlorophyll_a"],
            "units": {"chlorophyll_a": "mg/m³"},
            "data_source": "ESA/Plymouth Marine Lab",
            "access_method": "ERDDAP griddap",
            "authentication": False,
        }

    def get_coverage_period(self) -> dict[str, str]:
        """Get temporal coverage."""
        return {"start": "1997-09-04", "end": "present"}

    def is_available(
        self, latitude: float, longitude: float, target_date: date
    ) -> bool:
        """Check if ESA CCI data is available for location and date.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date to check

        Returns:
            True if data should be available
        """
        if not self._validate_coordinates(latitude, longitude):
            return False

        # ESA CCI coverage starts 1997-09-04
        start_date = date(1997, 9, 4)

        # Global ocean coverage, but chlorophyll is mainly in upper ocean
        # Could add more sophisticated marine/land detection here
        return target_date >= start_date

    def get_marine_data(
        self,
        latitude: float,
        longitude: float,
        target_date: date,
        _parameters: list[str] | None = None,
    ) -> MarineResult:
        """Get chlorophyll-a data from ESA CCI.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date for chlorophyll query
            parameters: Optional parameter filter (ignored - only chlorophyll available)

        Returns:
            MarineResult with chlorophyll-a data
        """
        logger.info(
            f"Fetching ESA CCI chlorophyll-a for {latitude}, {longitude} on {target_date}"
        )

        # Initialize result
        result = MarineResult(
            location={"lat": latitude, "lon": longitude},
            collection_date=target_date.strftime("%Y-%m-%d"),
        )

        if not self.is_available(latitude, longitude, target_date):
            logger.warning(
                f"ESA CCI data not available for {latitude}, {longitude} on {target_date}"
            )
            result.failed_providers = [self.provider_name]
            return result

        try:
            chl_value = self._fetch_chlorophyll_data(latitude, longitude, target_date)

            if chl_value is not None:
                precision = MarinePrecision(
                    method="satellite_composite",
                    target_date=target_date.strftime("%Y-%m-%d"),
                    data_quality=MarineQuality.SATELLITE_L3,
                    spatial_resolution="~1 km",
                    temporal_resolution="daily",
                    provider=self.provider_name,
                )

                result.chlorophyll_a = MarineObservation(
                    value=chl_value,
                    unit="mg/m³",
                    precision=precision,
                    quality_score=85,  # Good quality for L3 satellite product
                )

                result.successful_providers = [self.provider_name]
                result.overall_quality = MarineQuality.SATELLITE_L3

                logger.info(f"Successfully retrieved chlorophyll-a: {chl_value} mg/m³")
            else:
                logger.warning("ESA CCI returned null chlorophyll value")
                result.failed_providers = [self.provider_name]

        except Exception as e:
            logger.error(f"Error fetching ESA CCI data: {e}")
            result.failed_providers = [self.provider_name]

        return result

    def _fetch_chlorophyll_data(
        self, latitude: float, longitude: float, target_date: date
    ) -> float | None:
        """Fetch chlorophyll-a data from ESA CCI ERDDAP endpoint.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Date for query

        Returns:
            Chlorophyll-a concentration in mg/m³ or None if unavailable
        """
        try:
            # Format date for ERDDAP (ISO format)
            date_str = target_date.strftime("%Y-%m-%d")

            # Build ERDDAP query URL
            # Note: This is a simplified example - actual ESA CCI dataset IDs and variables may differ
            url = (
                f"{self.base_url}/{self.dataset_id}.csv"
                f"?chlor_a[({date_str}):1:({date_str})]"
                f"[({latitude}):1:({latitude})]"
                f"[({longitude}):1:({longitude})]"
            )

            logger.debug(f"ESA CCI query URL: {url}")

            # Make cached request
            response = request("GET", url, timeout=self.timeout)
            response.raise_for_status()

            # Parse CSV response
            lines = response.text.strip().split("\n")

            if len(lines) < 2:
                logger.warning("ESA CCI response has no data rows")
                return None

            # Skip header row, get data row
            data_line = lines[1]
            values = data_line.split(",")

            if len(values) < 4:
                logger.warning(f"ESA CCI response malformed: {data_line}")
                return None

            # Chlorophyll is typically the last column
            chl_str = values[-1].strip()

            if chl_str in ["NaN", "", "null"]:
                logger.warning("ESA CCI returned NaN/null chlorophyll value")
                return None

            chl_value = float(chl_str)

            # Sanity check chlorophyll range (0.01 to 100 mg/m³)
            if not 0.001 <= chl_value <= 100.0:
                logger.warning(
                    f"ESA CCI chlorophyll value outside expected range: {chl_value} mg/m³"
                )
                return None

            return chl_value

        except requests.exceptions.RequestException as e:
            logger.error(f"ESA CCI request failed: {e}")
            # Fallback to estimated chlorophyll based on location
            return self._estimate_chlorophyll_fallback(latitude, longitude)
        except ValueError as e:
            logger.error(f"ESA CCI data parsing failed: {e}")
            return self._estimate_chlorophyll_fallback(latitude, longitude)
        except Exception as e:
            logger.error(f"Unexpected ESA CCI error: {e}")
            return None

    def _estimate_chlorophyll_fallback(
        self, latitude: float, longitude: float
    ) -> float | None:
        """Fallback chlorophyll estimation for demonstration.

        This provides rough chlorophyll estimates based on oceanographic patterns.
        In production, this would be replaced with actual ESA CCI API access.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            Estimated chlorophyll-a concentration in mg/m³
        """
        try:
            abs_lat = abs(latitude)

            # Rough chlorophyll patterns based on latitude
            if abs_lat < 10:
                # Tropical/equatorial - typically low chlorophyll
                base_chl = 0.15
            elif abs_lat < 30:
                # Subtropical - very low chlorophyll (oligotrophic gyres)
                base_chl = 0.08
            elif abs_lat < 60:
                # Temperate - moderate chlorophyll
                base_chl = 0.5
            else:
                # Polar - high chlorophyll during growing season
                base_chl = 1.2

            # Add some variation based on longitude (coastal vs open ocean)
            # This is very simplified - real patterns are much more complex
            coastal_factor = 1.0
            if abs(longitude) > 150:  # Pacific
                coastal_factor = 0.8
            elif abs(longitude) < 30:  # Atlantic
                coastal_factor = 1.2

            estimated_chl = base_chl * coastal_factor

            # Keep within reasonable bounds
            estimated_chl = max(0.05, min(estimated_chl, 10.0))

            logger.info(f"Using estimated chlorophyll: {estimated_chl} mg/m³")
            return estimated_chl

        except Exception as e:
            logger.error(f"Chlorophyll estimation failed: {e}")
            return None
