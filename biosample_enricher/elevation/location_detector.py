"""Advanced location detection using multiple methods and fallbacks."""

import time
from typing import Any

from ..http_cache import request
from ..logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for external API calls."""

    def __init__(self) -> None:
        self.last_request_times: dict[str, float] = {}

    def wait_if_needed(self, service: str, min_interval: float = 1.1) -> None:
        """Ensure minimum interval between requests for a service."""
        now = time.time()
        last_time = self.last_request_times.get(service, 0)
        time_since_last = now - last_time

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting {service}: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_times[service] = time.time()


class LocationDetector:
    """
    Comprehensive location detection with multiple methods and fallbacks.

    Uses OSM Nominatim reverse geocoding as primary method, with fallbacks
    to heuristic-based detection for ocean areas and error cases.
    """

    def __init__(self, user_agent: str = "biosample-enricher/1.0"):
        """
        Initialize the location detector.

        Args:
            user_agent: User agent string for OSM Nominatim requests (required)
        """
        self.user_agent = user_agent
        self.rate_limiter = RateLimiter()
        self._cache: dict[tuple[float, float], dict[str, Any]] = {}
        logger.info("LocationDetector initialized with OSM Nominatim")

    def detect_location(
        self, lat: float, lon: float, prefer_online: bool = True
    ) -> dict[str, Any]:
        """
        Detect location characteristics using multiple methods.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            prefer_online: Whether to prefer online services over heuristics

        Returns:
            Dictionary with location information
        """
        # Round coordinates to reduce cache size and improve cache hits
        lat_rounded = round(lat, 4)
        lon_rounded = round(lon, 4)

        # Try online method first if preferred
        if prefer_online:
            result = self._detect_via_osm_nominatim(lat_rounded, lon_rounded)
            if result["method"] != "error":
                return result

        # Fall back to heuristic method
        return self._detect_via_heuristics(lat_rounded, lon_rounded)

    def _detect_via_osm_nominatim(self, lat: float, lon: float) -> dict[str, Any]:
        """
        Use OSM Nominatim reverse geocoding for location detection.

        This is the most accurate method for determining country and ocean areas.
        """
        try:
            # Respect rate limiting (1 req/sec for OSM Nominatim)
            self.rate_limiter.wait_if_needed("osm_nominatim", 1.1)

            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "zoom": 3,  # Country level
                "addressdetails": 1,
            }

            headers = {"User-Agent": self.user_agent}

            logger.debug(f"OSM Nominatim lookup for {lat:.4f}, {lon:.4f}")

            response = request(
                "GET",
                "https://nominatim.openstreetmap.org/reverse",
                params=params,
                headers=headers,
                timeout=10.0,
            )

            response.raise_for_status()
            data = response.json()

            # Check if we got country information
            if "address" in data and "country_code" in data["address"]:
                country_code = data["address"]["country_code"].upper()
                country_name = data["address"].get("country", "")

                logger.debug(f"OSM Nominatim found: {country_name} ({country_code})")

                # For US coordinates, use heuristic region detection
                region = None
                if country_code == "US":
                    _, region = self._check_us_territory_bounds(lat, lon)

                return {
                    "is_us_territory": country_code == "US",
                    "is_ocean": False,
                    "country_code": country_code,
                    "country_name": country_name,
                    "method": "osm_nominatim",
                    "confidence": 0.95,
                    "region": region,
                    "routing_hint": "us_land"
                    if country_code == "US"
                    else "international_land",
                }

            else:
                # No country found - likely ocean or disputed territory
                logger.debug("OSM Nominatim found no country - likely ocean")

                return {
                    "is_us_territory": False,
                    "is_ocean": True,
                    "country_code": None,
                    "country_name": "Ocean",
                    "method": "osm_nominatim",
                    "confidence": 0.9,
                    "region": None,
                    "routing_hint": "ocean",
                }

        except Exception as e:
            logger.warning(f"OSM Nominatim lookup failed: {e}")
            return {
                "is_us_territory": False,
                "is_ocean": False,
                "country_code": "ERROR",
                "country_name": f"Error: {str(e)}",
                "method": "error",
                "confidence": 0.0,
                "region": None,
                "routing_hint": "unknown",
            }

    def _detect_via_heuristics(self, lat: float, lon: float) -> dict[str, Any]:
        """
        Fall back to heuristic-based detection using coordinate ranges.

        This is faster but less accurate than OSM Nominatim.
        """
        logger.debug(f"Using heuristic detection for {lat:.4f}, {lon:.4f}")

        # Check if in US territory using coordinate bounds
        is_us, region = self._check_us_territory_bounds(lat, lon)

        # Check if likely ocean using large ocean area detection
        is_ocean = self._check_large_ocean_areas(lat, lon)

        if is_us:
            routing_hint = "ocean" if is_ocean else "us_land"
            country_name = "United States (Ocean)" if is_ocean else "United States"
        elif is_ocean:
            routing_hint = "ocean"
            country_name = "Ocean"
        else:
            routing_hint = "international_land"
            country_name = "International Land"

        return {
            "is_us_territory": is_us,
            "is_ocean": is_ocean,
            "country_code": "US" if is_us and not is_ocean else None,
            "country_name": country_name,
            "method": "heuristic",
            "confidence": 0.7,  # Lower confidence for heuristics
            "region": region,
            "routing_hint": routing_hint,
        }

    def _check_us_territory_bounds(
        self, lat: float, lon: float
    ) -> tuple[bool, str | None]:
        """Check if coordinates are in US territory using bounding boxes."""

        # Continental US (CONUS)
        if 24.396308 <= lat <= 49.384358 and -125.0 <= lon <= -66.93457:
            return True, "CONUS"

        # Alaska
        if (54.0 <= lat <= 71.5 and -180.0 <= lon <= -129.0) or (
            51.0 <= lat <= 55.5 and (lon >= 172.0 or lon <= -129.0)
        ):
            return True, "AK"

        # Hawaii
        if 18.0 <= lat <= 22.5 and -161.0 <= lon <= -154.0:
            return True, "HI"

        # Puerto Rico
        if 17.8 <= lat <= 18.6 and -67.5 <= lon <= -65.0:
            return True, "PR"

        # US Virgin Islands
        if 17.6 <= lat <= 18.5 and -65.2 <= lon <= -64.5:
            return True, "VI"

        # Guam
        if 13.2 <= lat <= 13.7 and 144.6 <= lon <= 145.0:
            return True, "GU"

        # American Samoa
        if -14.7 <= lat <= -14.0 and -171.2 <= lon <= -169.4:
            return True, "AS"

        # Northern Mariana Islands
        if 14.0 <= lat <= 20.6 and 144.8 <= lon <= 146.1:
            return True, "MP"

        return False, None

    def _check_large_ocean_areas(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in large ocean areas far from land."""

        # Central Pacific Ocean
        if -30 <= lat <= 30 and -180 <= lon <= -120:
            # Exclude coastal areas near Americas
            return not lon > -130

        # Central Atlantic Ocean
        if -40 <= lat <= 40 and -50 <= lon <= -10:
            return True

        # Southern Ocean (far from Antarctica)
        if lat < -60:
            return True

        # Central Indian Ocean
        return bool(-30 <= lat <= 10 and 60 <= lon <= 90)

    def classify_for_elevation_routing(self, lat: float, lon: float) -> dict[str, Any]:
        """
        Classify coordinates specifically for elevation service routing.

        Returns classification with recommended provider order.
        """
        location_info = self.detect_location(lat, lon)

        # Determine recommended providers based on classification
        recommended_providers = []

        if location_info["is_us_territory"]:
            if location_info["is_ocean"]:
                # US ocean areas - USGS likely won't work
                recommended_providers = ["google", "open_topo_data", "osm", "usgs"]
            else:
                # US land: USGS first
                recommended_providers = ["usgs", "google", "open_topo_data", "osm"]
                # Special case for Alaska and Hawaii - may have limited USGS coverage
                if location_info.get("region") in ["AK", "HI"]:
                    recommended_providers = ["usgs", "google", "open_topo_data", "osm"]
        else:
            # International locations
            if location_info["is_ocean"]:
                # International ocean - prioritize global providers
                recommended_providers = ["google", "open_topo_data", "osm"]
            else:
                # International land - Open Topo Data has excellent global coverage
                recommended_providers = ["google", "open_topo_data", "osm"]

        # Add is_land field (inverse of is_ocean)
        result = {**location_info, "recommended_providers": recommended_providers}
        result["is_land"] = (
            None if location_info["is_ocean"] is None else not location_info["is_ocean"]
        )
        return result
