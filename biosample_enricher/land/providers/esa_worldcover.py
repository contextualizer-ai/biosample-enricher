"""ESA WorldCover land cover provider."""

from datetime import date

from biosample_enricher.http_cache import get_session
from biosample_enricher.land.models import LandCoverObservation
from biosample_enricher.land.providers.base import LandCoverProviderBase
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class ESAWorldCoverProvider(LandCoverProviderBase):
    """ESA WorldCover land cover provider.

    Provides global land cover classification at 10m resolution.
    Uses ESA WorldCover data via WMS and REST APIs.

    Data source: https://worldcover2021.esa.int/
    """

    def __init__(self, timeout: int = 30):
        self.wms_base = "https://services.terrascope.be/wms/v2"
        self.timeout = timeout
        self._session = get_session()

        # ESA WorldCover classification mapping
        self.class_mapping = {
            10: "Tree cover",
            20: "Shrubland",
            30: "Grassland",
            40: "Cropland",
            50: "Built-up",
            60: "Bare / sparse vegetation",
            70: "Snow and ice",
            80: "Permanent water bodies",
            90: "Herbaceous wetland",
            95: "Mangroves",
            100: "Moss and lichen",
        }

    @property
    def name(self) -> str:
        return "ESA WorldCover"

    @property
    def coverage_description(self) -> str:
        return "Global land cover at 10m resolution (2020-2021)"

    def is_available(self) -> bool:
        """Check if ESA WorldCover WMS is available."""
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
        """Get ESA WorldCover land cover data.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            target_date: Target date (used for temporal offset calculation)

        Returns:
            List containing single LandCoverObservation if successful
        """
        self.validate_coordinates(latitude, longitude)

        try:
            # Use WMS GetFeatureInfo to query land cover at point
            class_code = self._query_land_cover_wms(latitude, longitude)

            if class_code is None:
                return []

            # Get class label
            class_label = self.class_mapping.get(class_code, f"Unknown ({class_code})")

            # Calculate temporal offset (ESA WorldCover 2021 represents 2020-2021)
            data_date = date(2021, 1, 1)  # Representative date
            temporal_offset = None
            if target_date:
                temporal_offset = (data_date - target_date).days

            observation = LandCoverObservation(
                provider=self.name,
                actual_location={"lat": latitude, "lon": longitude},
                distance_m=5.0,  # 10m resolution -> ~5m to pixel center
                actual_date=data_date,
                temporal_offset_days=temporal_offset,
                class_code=str(class_code),
                class_label=class_label,
                classification_system="ESA WorldCover 2021",
                confidence=0.85,  # Generally high quality global product
                resolution_m=10.0,
                dataset_version="2021",
                quality_flags=["satellite_derived"],
            )

            logger.info(
                f"Retrieved ESA WorldCover data for ({latitude}, {longitude}): "
                f"{class_label} (code {class_code})"
            )

            return [observation]

        except Exception as e:
            logger.error(f"Error retrieving ESA WorldCover data: {e}")
            return []

    def _query_land_cover_wms(self, latitude: float, longitude: float) -> int | None:
        """Query land cover class using WMS GetFeatureInfo.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            Land cover class code or None if no data
        """
        # Create small bounding box around point
        buffer = 0.0001  # Small buffer for point query
        bbox = f"{longitude - buffer},{latitude - buffer},{longitude + buffer},{latitude + buffer}"

        params = {
            "SERVICE": "WMS",
            "REQUEST": "GetFeatureInfo",
            "VERSION": "1.3.0",
            "LAYERS": "WORLDCOVER_2021_MAP",
            "QUERY_LAYERS": "WORLDCOVER_2021_MAP",
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
            # Response format varies by WMS server
            if "features" in data and data["features"]:
                feature = data["features"][0]
                properties = feature.get("properties", {})

                # Try common property names for land cover value
                for key in ["DN", "value", "class", "landcover", "WORLDCOVER_2021_MAP"]:
                    if key in properties:
                        value = properties[key]
                        if isinstance(value, int | float) and value > 0:
                            return int(value)

            return None

        except Exception as e:
            logger.debug(f"WMS query failed: {e}")
            return None
