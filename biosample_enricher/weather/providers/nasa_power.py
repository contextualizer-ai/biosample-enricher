"""
NASA POWER weather provider for climate normals.

Provides access to NASA POWER (Prediction Of Worldwide Energy Resources) API
for 20-year climatologies (2001-2020) globally at 0.5° x 0.625° resolution.
"""

from biosample_enricher.http_cache import get_session
from biosample_enricher.logging_config import get_logger
from biosample_enricher.weather.models import ClimateNormalsResult

logger = get_logger(__name__)


class NASAPowerProvider:
    """
    NASA POWER - MERRA-2 satellite reanalysis

    Technical Characteristics:
        API Type: REST
        Endpoint: https://power.larc.nasa.gov/api/temporal/climatology/point
        Authentication: none
        Coverage: Global
        Resolution: 0.5° x 0.625° (~50-60km grid)
        Temporal: 2001-2020 (climatologies)
        Freshness: Static climatologies

    Reliability:
        Stability: HIGH
        Data Quality: satellite_reanalysis
        Uptime: Excellent (NASA operational service)
        Known Issues:
            - Only provides 2001-2020 period (not WMO standard 1991-2020)
            - Coarser spatial resolution than station data

    Cost:
        Model: free
        Free Tier: Unlimited

    Strengths:
        ✓ True global coverage (satellite-based)
        ✓ No API key required
        ✓ Works anywhere on Earth (deserts, mountains, oceans)
        ✓ Consistent methodology globally
        ✓ High stability (NASA/GMAO service)
        ✓ Fast response (pre-computed)

    Weaknesses:
        ✗ Shorter period (20 years: 2001-2020 vs standard 30 years)
        ✗ Coarser resolution (0.5° × 0.625° vs station point data)
        ✗ Satellite bias in complex terrain
        ✗ Not WMO standard period
        ✗ Model-based (not direct measurements)

    Best For:
        • Remote locations far from weather stations
        • Ocean/marine samples
        • Global-scale studies requiring consistent methodology
        • Validation/comparison against station data

    Not Suitable For:
        • Urban areas with local station (prefer Meteostat)
        • Studies requiring WMO standard 1991-2020 period

    Complements:
        • Meteostat (for station-rich areas)

    NMDC Integration:
        Schema Slots: annual_precpt, annual_temp
        Role: fallback_for_remote_areas
        Excellent For: oceans, deserts, mountains, antarctica, remote_regions

    See Also:
        Full comparison: config/provider_metadata.yaml
        API: https://power.larc.nasa.gov/api/temporal/climatology/point
    """

    def __init__(self, timeout: int = 30):
        """Initialize NASA POWER provider."""
        self.timeout = timeout
        self.provider_name = "nasa_power"
        self.base_url = "https://power.larc.nasa.gov/api/temporal/climatology/point"

    def get_climate_normals(
        self,
        lat: float,
        lon: float,
        start_year: int = 2001,
        end_year: int = 2020,
    ) -> ClimateNormalsResult:
        """
        Get 20-year climate averages from NASA POWER.

        Note: NASA POWER provides 2001-2020 climatologies (20-year period),
        not the standard 1991-2020 (30-year period). The start_year and
        end_year parameters are ignored - NASA POWER only provides the
        fixed 2001-2020 period.

        Args:
            lat: Latitude in decimal degrees (-90 to 90)
            lon: Longitude in decimal degrees (-180 to 180)
            start_year: Ignored (NASA POWER uses 2001-2020)
            end_year: Ignored (NASA POWER uses 2001-2020)

        Returns:
            ClimateNormalsResult with monthly climate averages

        Raises:
            ValueError: If API request fails or no data available

        Example:
            >>> provider = NASAPowerProvider()
            >>> result = provider.get_climate_normals(37.7749, -122.4194)
            >>> annual_temp = result.get_annual_temperature()
            >>> print(f"San Francisco: {annual_temp}°C average")
            San Francisco: 13.58°C average
        """
        logger.info(
            f"Fetching NASA POWER climate normals for ({lat}, {lon}) period 2001-2020"
        )

        if start_year != 2001 or end_year != 2020:
            logger.warning(
                f"NASA POWER only provides 2001-2020 climatologies. "
                f"Requested {start_year}-{end_year} will be ignored."
            )

        # Build API request
        params = {
            "parameters": "T2M,PRECTOTCORR",  # Temperature and precipitation
            "community": "AG",  # Agroclimatology community
            "longitude": lon,
            "latitude": lat,
            "format": "JSON",
        }

        session = get_session()
        try:
            response = session.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"NASA POWER API returned data for ({lat}, {lon})")

            # Extract climate data
            parameters = data.get("properties", {}).get("parameter", {})

            if not parameters:
                raise ValueError("No climate data returned from NASA POWER API")

            # Extract monthly temperature (T2M in Celsius)
            temp_data = parameters.get("T2M", {})

            # Extract monthly precipitation (PRECTOTCORR in mm/day)
            precip_data = parameters.get("PRECTOTCORR", {})

            # Convert to lists format expected by ClimateNormalsResult
            month_names = [
                "JAN",
                "FEB",
                "MAR",
                "APR",
                "MAY",
                "JUN",
                "JUL",
                "AUG",
                "SEP",
                "OCT",
                "NOV",
                "DEC",
            ]

            monthly_precipitation = []
            monthly_temperature = []
            days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

            for month_idx, month_name in enumerate(month_names):
                # Temperature is already in Celsius
                temp_celsius = temp_data.get(month_name)
                monthly_temperature.append(temp_celsius)

                # Precipitation is in mm/day, convert to mm/month
                precip_mm_day = precip_data.get(month_name)
                if precip_mm_day is not None:
                    precip_mm_month = precip_mm_day * days_in_month[month_idx]
                    monthly_precipitation.append(precip_mm_month)
                else:
                    monthly_precipitation.append(None)

            if not any(monthly_precipitation) or not any(monthly_temperature):
                raise ValueError("No valid monthly data extracted from NASA POWER")

            return ClimateNormalsResult(
                monthly_precipitation=monthly_precipitation,
                monthly_temperature=monthly_temperature,
                station_id="NASA_POWER_GRID",  # Satellite data, no physical station
                station_distance_km=0.0,  # Gridded data
                location={"lat": lat, "lon": lon},
                normals_period=(2001, 2020),
                provider="nasa_power",
                data_quality="MERRA-2 satellite reanalysis, 20-year climatology (2001-2020)",
            )

        except Exception as e:
            logger.error(f"NASA POWER API error for ({lat}, {lon}): {e}")
            raise ValueError(f"Failed to get NASA POWER climate normals: {e}") from e
