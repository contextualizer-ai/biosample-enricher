"""Geographic coordinate classification for elevation service."""

from ..logging_config import get_logger
from ..models import CoordinateClassification
from .location_detector import LocationDetector

logger = get_logger(__name__)


class CoordinateClassifier:
    """Classifies geographic coordinates for provider routing."""

    def __init__(
        self,
        enable_online_detection: bool = True,
        user_agent: str = "biosample-enricher/1.0",
    ) -> None:
        """
        Initialize the coordinate classifier.

        Args:
            enable_online_detection: Whether to use online services like OSM Nominatim
            user_agent: User agent string for online requests
        """
        self.enable_online_detection = enable_online_detection
        self.location_detector: LocationDetector | None
        if enable_online_detection:
            self.location_detector = LocationDetector(user_agent=user_agent)
            logger.debug("Initialized CoordinateClassifier with online detection")
        else:
            self.location_detector = None
            logger.debug("Initialized CoordinateClassifier with heuristics only")

    def classify(self, lat: float, lon: float) -> CoordinateClassification:
        """
        Classify coordinates to determine appropriate providers.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Classification result
        """
        logger.debug(f"Classifying coordinates: {lat:.6f}, {lon:.6f}")

        # Use enhanced location detector if available
        if self.location_detector:
            try:
                location_info = self.location_detector.detect_location(lat, lon)

                classification = CoordinateClassification(
                    is_us_territory=location_info["is_us_territory"],
                    region=location_info.get("region"),
                    confidence=location_info["confidence"],
                    is_land=None
                    if location_info["is_ocean"] is None
                    else not location_info["is_ocean"],
                )

                logger.debug(
                    f"Enhanced classification: US={classification.is_us_territory}, "
                    f"region={classification.region}, land={classification.is_land}, "
                    f"confidence={classification.confidence:.3f}, method={location_info['method']}"
                )
                return classification

            except Exception as e:
                logger.warning(
                    f"Enhanced location detection failed, falling back to heuristics: {e}"
                )

        # Fall back to heuristic method
        is_us, region, confidence = self._classify_us_territory(lat, lon)
        is_likely_land = self._classify_land_vs_ocean(lat, lon)

        classification = CoordinateClassification(
            is_us_territory=is_us,
            region=region,
            confidence=confidence,
            is_land=is_likely_land,
        )

        logger.debug(
            f"Heuristic classification: US={is_us}, region={region}, land={is_likely_land}, confidence={confidence:.3f}"
        )
        return classification

    def _classify_us_territory(
        self, lat: float, lon: float
    ) -> tuple[bool, str | None, float]:
        """
        Determine if coordinates are within US territory.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Tuple of (is_us_territory, region_code, confidence)
        """
        # Continental US (CONUS) - approximate bounding box
        if self._in_conus(lat, lon):
            return True, "CONUS", 0.95

        # Alaska
        if self._in_alaska(lat, lon):
            return True, "AK", 0.95

        # Hawaii
        if self._in_hawaii(lat, lon):
            return True, "HI", 0.95

        # Puerto Rico
        if self._in_puerto_rico(lat, lon):
            return True, "PR", 0.95

        # US Virgin Islands
        if self._in_usvi(lat, lon):
            return True, "VI", 0.95

        # Guam
        if self._in_guam(lat, lon):
            return True, "GU", 0.95

        # American Samoa
        if self._in_american_samoa(lat, lon):
            return True, "AS", 0.95

        # Northern Mariana Islands
        if self._in_northern_marianas(lat, lon):
            return True, "MP", 0.95

        # Not in US territory
        return False, None, 0.95

    def _in_conus(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in Continental US."""
        # Approximate bounding box for CONUS
        return 24.396308 <= lat <= 49.384358 and -125.0 <= lon <= -66.93457

    def _in_alaska(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in Alaska."""
        # Alaska main landmass
        if 54.0 <= lat <= 71.5 and -180.0 <= lon <= -129.0:
            return True
        # Aleutian Islands (crosses 180° meridian)
        return bool(51.0 <= lat <= 55.5 and (lon >= 172.0 or lon <= -129.0))

    def _in_hawaii(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in Hawaii."""
        return 18.0 <= lat <= 22.5 and -161.0 <= lon <= -154.0

    def _in_puerto_rico(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in Puerto Rico."""
        return 17.8 <= lat <= 18.6 and -67.5 <= lon <= -65.0

    def _in_usvi(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in US Virgin Islands."""
        return 17.6 <= lat <= 18.5 and -65.2 <= lon <= -64.5

    def _in_guam(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in Guam."""
        return 13.2 <= lat <= 13.7 and 144.6 <= lon <= 145.0

    def _in_american_samoa(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in American Samoa."""
        return -14.7 <= lat <= -14.0 and -171.2 <= lon <= -169.4

    def _in_northern_marianas(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in Northern Mariana Islands."""
        return 14.0 <= lat <= 20.6 and 144.8 <= lon <= 146.1

    def _classify_land_vs_ocean(self, lat: float, lon: float) -> bool | None:
        """
        Classify if coordinates are likely on land vs ocean using heuristics.

        This is a basic heuristic-based approach for Phase 1. More sophisticated
        methods could use coastline databases or land/ocean masks.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            True if likely land, False if likely ocean, None if uncertain
        """
        # Very basic heuristics - this can be enhanced later

        # Large open ocean areas (very high confidence ocean)
        if self._is_large_ocean_area(lat, lon):
            return False

        # Known land areas (continental masses)
        if self._is_major_landmass(lat, lon):
            return True

        # Close to known coastlines - uncertain
        return None

    def _is_large_ocean_area(self, lat: float, lon: float) -> bool:
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

    def _is_major_landmass(self, lat: float, lon: float) -> bool:
        """Check if coordinates are in major continental landmasses."""

        # North American continent (excluding coasts)
        if 30 <= lat <= 60 and -120 <= lon <= -75:
            return True

        # South American continent
        if -40 <= lat <= 10 and -75 <= lon <= -35:
            return True

        # African continent
        if -30 <= lat <= 30 and 10 <= lon <= 45:
            return True

        # European continent
        if 35 <= lat <= 65 and -5 <= lon <= 40:
            return True

        # Asian continent
        if 20 <= lat <= 65 and 60 <= lon <= 140:
            return True

        # Australian continent
        return bool(-40 <= lat <= -15 and 115 <= lon <= 150)

    def classify_biosample_location(self, lat: float, lon: float) -> dict:
        """
        Classify a biosample location for routing and metadata.

        This method provides biosample-specific classification that can be
        stored with the sample metadata for efficient provider routing.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Dictionary with classification metadata
        """
        # Use enhanced location detector if available for more detailed routing
        if self.location_detector:
            try:
                return self.location_detector.classify_for_elevation_routing(lat, lon)
            except Exception as e:
                logger.warning(
                    f"Enhanced biosample classification failed, using fallback: {e}"
                )

        # Fall back to basic classification
        classification = self.classify(lat, lon)

        # Determine recommended providers based on classification
        recommended_providers = []

        if classification.is_us_territory:
            recommended_providers.append("usgs")
            if classification.region in ["AK", "HI"]:
                # Alaska and Hawaii may have less USGS coverage
                recommended_providers.extend(["google", "open_topo_data", "osm"])
            else:
                recommended_providers.extend(["google", "open_topo_data"])
        else:
            # International locations
            recommended_providers.extend(["google", "open_topo_data", "osm"])

        # If likely ocean, deprioritize USGS
        if classification.is_land is False and "usgs" in recommended_providers:
            recommended_providers.remove("usgs")
            recommended_providers.append("usgs")  # Move to end

        return {
            "is_us_territory": classification.is_us_territory,
            "region": classification.region,
            "is_land": classification.is_land,
            "confidence": classification.confidence,
            "recommended_providers": recommended_providers,
            "routing_hint": self._get_routing_hint(classification),
        }

    def _get_routing_hint(self, classification: CoordinateClassification) -> str:
        """Get a routing hint for efficient provider selection."""
        if classification.is_land is False:
            return "ocean"
        elif classification.is_us_territory:
            return "us_land"
        else:
            return "international_land"
