"""NLCD (National Land Cover Database) provider for US land cover."""

from datetime import date

from biosample_enricher.http_cache import get_session
from biosample_enricher.land.models import LandCoverObservation
from biosample_enricher.land.providers.base import LandCoverProviderBase
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class NLCDProvider(LandCoverProviderBase):
    """NLCD (National Land Cover Database) provider.

    Provides US land cover classification at 30m resolution.
    Uses USGS NLCD data via WMS/COG access.

    Data source: https://www.usgs.gov/centers/eros/science/national-land-cover-database
    """

    def __init__(self, timeout: int = 30):
        self.wms_base = "https://www.mrlc.gov/geoserver/mrlc_display/wms"
        self.timeout = timeout
        self._session = get_session()

        # NLCD classification mapping (2019/2021 classes)
        self.class_mapping = {
            11: "Open Water",
            12: "Perennial Ice/Snow",
            21: "Developed, Open Space",
            22: "Developed, Low Intensity",
            23: "Developed, Medium Intensity",
            24: "Developed, High Intensity",
            31: "Barren Land (Rock/Sand/Clay)",
            41: "Deciduous Forest",
            42: "Evergreen Forest",
            43: "Mixed Forest",
            51: "Dwarf Scrub",
            52: "Shrub/Scrub",
            71: "Grassland/Herbaceous",
            72: "Sedge/Herbaceous",
            73: "Lichens",
            74: "Moss",
            81: "Pasture/Hay",
            82: "Cultivated Crops",
            90: "Woody Wetlands",
            95: "Emergent Herbaceous Wetlands",
        }

        # Available NLCD years and their WMS layer names
        self.nlcd_layers = {
            2021: "NLCD_2021_Land_Cover_L48",
            2019: "NLCD_2019_Land_Cover_L48",
            2016: "NLCD_2016_Land_Cover_L48",
            2011: "NLCD_2011_Land_Cover_L48",
            2006: "NLCD_2006_Land_Cover_L48",
            2001: "NLCD_2001_Land_Cover_L48",
        }

    @property
    def name(self) -> str:
        return "NLCD"

    @property
    def coverage_description(self) -> str:
        return "US land cover at 30m resolution (2001-2021, multi-year)"

    def is_available(self) -> bool:
        """Check if NLCD WMS is available."""
        try:
            # Test WMS GetCapabilities
            params = {
                "SERVICE": "WMS",
                "REQUEST": "GetCapabilities",
                "VERSION": "1.3.0",
            }
            response = self._session.get(self.wms_base, params=params, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_land_cover(
        self, latitude: float, longitude: float, target_date: date | None = None
    ) -> list[LandCoverObservation]:
        """Get NLCD land cover data.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Target date for temporal alignment

        Returns:
            List of LandCoverObservation from available NLCD years
        """
        self.validate_coordinates(latitude, longitude)

        # Check if location is within US bounds (approximate)
        if not self._is_us_location(latitude, longitude):
            logger.debug(f"Location ({latitude}, {longitude}) is outside US bounds")
            return []

        observations = []

        # Determine which NLCD years to query based on target date
        years_to_query = self._select_nlcd_years(target_date)

        for year in years_to_query:
            try:
                obs = self._query_nlcd_year(latitude, longitude, year, target_date)
                if obs:
                    observations.append(obs)

            except Exception as e:
                logger.warning(f"Failed to query NLCD {year}: {e}")
                continue

        logger.info(
            f"Retrieved {len(observations)} NLCD observations "
            f"for ({latitude}, {longitude})"
        )

        return observations

    def _is_us_location(self, latitude: float, longitude: float) -> bool:
        """Check if location is within approximate US bounds."""
        # US bounding box (approximate, excludes territories)
        us_bounds = [
            (24.0, -125.0, 50.0, -66.0),  # Continental US
            (60.0, -180.0, 72.0, -140.0),  # Alaska
            (18.0, -161.0, 23.0, -154.0),  # Hawaii
        ]

        for min_lat, min_lon, max_lat, max_lon in us_bounds:
            if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
                return True

        return False

    def _select_nlcd_years(self, target_date: date | None) -> list[int]:
        """Select which NLCD years to query based on target date.

        Strategy: Return closest year <= target_date, plus next closest for comparison
        """
        available_years = sorted(self.nlcd_layers.keys())

        if target_date is None:
            # No target date - return most recent year
            return [available_years[-1]]

        target_year = target_date.year

        # Find closest year <= target year
        closest_years = []
        for year in reversed(available_years):
            if year <= target_year:
                closest_years.append(year)
                break

        # If no past year found, use earliest available
        if not closest_years:
            closest_years.append(available_years[0])

        # Add one more year for temporal comparison if available
        if len(available_years) > 1:
            for year in available_years:
                if year not in closest_years:
                    closest_years.append(year)
                    break

        return closest_years[:2]  # Limit to 2 years max

    def _query_nlcd_year(
        self, latitude: float, longitude: float, year: int, target_date: date | None
    ) -> LandCoverObservation | None:
        """Query NLCD data for a specific year."""
        if year not in self.nlcd_layers:
            logger.warning(f"NLCD year {year} not available")
            return None

        layer_name = self.nlcd_layers[year]

        try:
            # Query land cover class using WMS GetFeatureInfo
            class_code = self._query_nlcd_wms(latitude, longitude, layer_name)

            if class_code is None:
                return None

            # Get class label
            class_label = self.class_mapping.get(class_code, f"Unknown ({class_code})")

            # Calculate temporal offset
            data_date = date(year, 7, 1)  # Use mid-year as representative date
            temporal_offset = None
            if target_date:
                temporal_offset = (data_date - target_date).days

            # Calculate confidence based on temporal distance
            confidence = 0.85  # Base confidence for NLCD
            if temporal_offset is not None:
                # Reduce confidence for temporal distance
                years_diff = abs(temporal_offset) / 365.25
                confidence = max(0.5, confidence - (years_diff * 0.1))

            observation = LandCoverObservation(
                provider=f"{self.name} {year}",
                actual_location={"lat": latitude, "lon": longitude},
                distance_m=15.0,  # 30m resolution -> ~15m to pixel center
                actual_date=data_date,
                temporal_offset_days=temporal_offset,
                class_code=str(class_code),
                class_label=class_label,
                classification_system=f"NLCD {year}",
                confidence=confidence,
                resolution_m=30.0,
                dataset_version=str(year),
                quality_flags=["satellite_derived", "us_authoritative"],
            )

            logger.debug(
                f"Retrieved NLCD {year} data: {class_label} (code {class_code})"
            )

            return observation

        except Exception as e:
            logger.error(f"Error querying NLCD {year}: {e}")
            return None

    def _query_nlcd_wms(
        self, latitude: float, longitude: float, layer_name: str
    ) -> int | None:
        """Query NLCD land cover class using WMS GetFeatureInfo."""
        # Create small bounding box around point
        buffer = 0.0001
        bbox = f"{longitude - buffer},{latitude - buffer},{longitude + buffer},{latitude + buffer}"

        params = {
            "SERVICE": "WMS",
            "REQUEST": "GetFeatureInfo",
            "VERSION": "1.3.0",
            "LAYERS": layer_name,
            "QUERY_LAYERS": layer_name,
            "INFO_FORMAT": "application/json",
            "CRS": "EPSG:4326",
            "BBOX": bbox,
            "WIDTH": "1",
            "HEIGHT": "1",
            "I": "0",
            "J": "0",
        }

        try:
            response = self._session.get(
                self.wms_base, params=params, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Parse response to extract land cover value
            if "features" in data and data["features"]:
                feature = data["features"][0]
                properties = feature.get("properties", {})

                # Try common property names for land cover value
                for key in ["GRAY_INDEX", "value", "class", "landcover", layer_name]:
                    if key in properties:
                        value = properties[key]
                        if isinstance(value, int | float) and value > 0:
                            return int(value)

            return None

        except Exception as e:
            logger.debug(f"NLCD WMS query failed: {e}")
            return None
