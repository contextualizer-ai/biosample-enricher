"""ISRIC SoilGrids provider for global soil properties and classification."""

import math

import numpy as np
from rasterio.io import MemoryFile  # type: ignore[import-untyped]

from biosample_enricher.http_cache import get_session
from biosample_enricher.logging_config import get_logger
from biosample_enricher.soil.models import SoilObservation, SoilResult, classify_texture
from biosample_enricher.soil.providers.base import SoilProviderBase

logger = get_logger(__name__)


class SoilGridsProvider(SoilProviderBase):
    """ISRIC SoilGrids provider for global soil properties and WRB classification.

    Provides global soil data at 250m resolution including:
    - WRB soil classification
    - Soil properties (pH, organic carbon, texture, bulk density)
    - Derived texture classification using USDA triangle

    API Documentation: https://www.isric.org/web-coverage-services-wcs
    """

    def __init__(self, timeout: int = 30):
        self.wcs_base = "https://maps.isric.org/mapserv?map=/map/{service}.map"
        self.rest_base = "https://rest.isric.org/soilgrids/v2.0"
        self.timeout = timeout
        self._session = get_session()

        # WRB classification mapping
        self.wrb_codes = {
            0: "Acrisols",
            1: "Albeluvisols",
            2: "Alisols",
            3: "Andosols",
            4: "Arenosols",
            5: "Calcisols",
            6: "Cambisols",
            7: "Chernozems",
            8: "Cryosols",
            9: "Durisols",
            10: "Ferralsols",
            11: "Fluvisols",
            12: "Gleysols",
            13: "Gypsisols",
            14: "Histosols",
            15: "Kastanozems",
            16: "Leptosols",
            17: "Lixisols",
            18: "Luvisols",
            19: "Nitisols",
            20: "Phaeozems",
            21: "Planosols",
            22: "Plinthosols",
            23: "Podzols",
            24: "Regosols",
            25: "Solonchaks",
            26: "Solonetz",
            27: "Stagnosols",
            28: "Umbrisols",
            29: "Vertisols",
        }

        # Property scaling factors (SoilGrids uses scaled integers)
        self.scaling = {
            "phh2o": 0.1,  # pH scaled by 10
            "clay": 0.1,  # g/kg scaled by 10
            "sand": 0.1,  # g/kg scaled by 10
            "silt": 0.1,  # g/kg scaled by 10
            "soc": 0.1,  # dg/kg scaled by 10
            "bdod": 0.01,  # g/cm³ scaled by 100
            "nitrogen": 0.01,  # g/kg scaled by 100
        }

    @property
    def name(self) -> str:
        return "ISRIC SoilGrids"

    @property
    def coverage_description(self) -> str:
        return "Global coverage at 250m resolution - WRB classification and soil properties"

    def is_available(self) -> bool:
        """Check if SoilGrids services are available."""
        try:
            # Test REST endpoint first (faster)
            test_url = f"{self.rest_base}/classification/query"
            params = {"lat": 0, "lon": 0}
            response = self._session.get(test_url, params=params, timeout=5)
            return response.status_code == 200
        except Exception:
            # Fallback to WCS test
            try:
                test_url = self.wcs_base.format(service="wrb")
                wcs_params: dict[str, str] = {
                    "SERVICE": "WCS",
                    "REQUEST": "GetCapabilities",
                }
                response = self._session.get(test_url, params=wcs_params, timeout=5)
                return response.status_code == 200
            except Exception:
                return False

    def get_soil_data(
        self, latitude: float, longitude: float, depth_cm: str | None = "0-5cm"
    ) -> SoilResult:
        """Get SoilGrids soil data for a location.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            depth_cm: Depth interval (e.g., "0-5cm", "5-15cm")

        Returns:
            SoilResult with WRB classification and soil properties
        """
        self.validate_coordinates(latitude, longitude)

        try:
            observations = []
            warnings = []

            # Get WRB classification
            wrb_data = self._get_wrb_classification(latitude, longitude)

            # Get soil properties for the specified depth
            depth_str = depth_cm or "0-5cm"
            properties = self._get_soil_properties(latitude, longitude, depth_str)

            # Create observation combining classification and properties
            if wrb_data or properties:
                obs = SoilObservation(
                    classification_usda=None,
                    classification_wrb=wrb_data.get("classification"),
                    confidence_usda=None,
                    confidence_wrb=wrb_data.get("confidence"),
                    ph_h2o=properties.get("ph"),
                    organic_carbon=properties.get("soc"),
                    bulk_density=properties.get("bdod"),
                    sand_percent=properties.get("sand"),
                    silt_percent=properties.get("silt"),
                    clay_percent=properties.get("clay"),
                    texture_class=None,
                    total_nitrogen=properties.get("nitrogen"),
                    available_phosphorus=None,
                    cation_exchange_capacity=None,
                    depth_cm=depth_cm or "0-5cm",
                    measurement_method="ISRIC SoilGrids WCS/REST",
                )

                # Calculate texture class if we have texture data
                if all(properties.get(x) is not None for x in ["sand", "silt", "clay"]):
                    try:
                        texture_class = classify_texture(
                            properties["sand"], properties["silt"], properties["clay"]
                        )
                        obs.texture_class = texture_class
                    except ValueError as e:
                        warnings.append(f"Texture classification failed: {e}")

                observations.append(obs)

            # Calculate quality score
            distance_m = wrb_data.get("distance_m") or properties.get("distance_m") or 0
            data_completeness = self._calculate_completeness(wrb_data, properties)
            quality_score = self.calculate_quality_score(
                distance_m=distance_m, data_completeness=data_completeness
            )

            logger.info(
                f"Retrieved SoilGrids data for ({latitude}, {longitude}): {len(observations)} observations"
            )

            return SoilResult(
                latitude=latitude,
                longitude=longitude,
                distance_m=distance_m,
                observations=observations,
                quality_score=quality_score,
                provider=self.name,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Error retrieving SoilGrids data: {e}")
            return SoilResult(
                latitude=latitude,
                longitude=longitude,
                distance_m=0.0,
                observations=[],
                quality_score=0.0,
                provider=self.name,
                errors=[str(e)],
            )

    def _get_wrb_classification(self, latitude: float, longitude: float) -> dict:
        """Get WRB soil classification using REST API."""
        try:
            url = f"{self.rest_base}/classification/query"
            params = {"lat": latitude, "lon": longitude}

            logger.debug(
                f"Querying SoilGrids WRB classification at ({latitude}, {longitude})"
            )

            response = self._session.get(url, params=params, timeout=self.timeout)

            if not response.ok:
                logger.warning(
                    f"SoilGrids REST classification query failed: {response.status_code}"
                )
                return {}

            data = response.json()

            # Parse WRB classification from response
            if "properties" in data and "wrb_class_name" in data["properties"]:
                classification = data["properties"]["wrb_class_name"]
                probability = data["properties"].get("wrb_class_probability", 0) / 100.0

                logger.debug(
                    f"Found WRB classification: {classification} ({probability:.2f})"
                )

                return {
                    "classification": classification,
                    "confidence": probability,
                    "distance_m": 125.0,  # SoilGrids 250m resolution -> ~125m to center
                }

            return {}

        except Exception as e:
            logger.warning(f"Error getting WRB classification: {e}")
            # Fallback to WCS method
            return self._get_wrb_classification_wcs(latitude, longitude)

    def _get_wrb_classification_wcs(self, latitude: float, longitude: float) -> dict:
        """Get WRB classification using WCS (fallback method)."""
        try:
            # Get WRB MostProbable raster data
            coverage_id = "MostProbable"
            tiff_data = self._get_wcs_coverage("wrb", coverage_id, latitude, longitude)

            if not tiff_data:
                return {}

            # Parse raster data
            with MemoryFile(tiff_data) as mem, mem.open() as dataset:
                # Get pixel value at location
                row, col = dataset.index(longitude, latitude)
                row = int(np.clip(row, 0, dataset.height - 1))
                col = int(np.clip(col, 0, dataset.width - 1))

                # Read the value
                arr = dataset.read(1)
                wrb_code = int(arr[row, col])

                # Get center coordinates of pixel
                pixel_lon, pixel_lat = dataset.xy(row, col, offset="center")
                distance_m = self._haversine_distance(
                    latitude, longitude, float(pixel_lat), float(pixel_lon)
                )

                # Map code to classification
                classification = self.wrb_codes.get(wrb_code, f"Unknown({wrb_code})")

                return {
                    "classification": classification,
                    "confidence": 0.8,  # Default confidence for WCS
                    "distance_m": distance_m,
                }

        except Exception as e:
            logger.warning(f"Error getting WRB classification via WCS: {e}")
            return {}

    def _get_soil_properties(
        self, latitude: float, longitude: float, depth_cm: str
    ) -> dict:
        """Get soil properties using WCS."""
        properties = {}

        # Define properties to fetch
        property_ids = ["phh2o", "clay", "sand", "silt", "soc", "bdod", "nitrogen"]
        stat = "Q0.5"  # Median values

        for prop_id in property_ids:
            try:
                coverage_id = f"{prop_id}_{depth_cm}_{stat}"
                tiff_data = self._get_wcs_coverage(
                    prop_id, coverage_id, latitude, longitude
                )

                if tiff_data:
                    value = self._extract_pixel_value(tiff_data, latitude, longitude)
                    if value is not None:
                        # Apply scaling factor
                        scaling_factor = self.scaling.get(prop_id, 1.0)
                        scaled_value = value * scaling_factor
                        properties[prop_id] = round(scaled_value, 2)

                        # Calculate distance for first successful property
                        if "distance_m" not in properties:
                            distance_m = self._calculate_pixel_distance(
                                tiff_data, latitude, longitude
                            )
                            properties["distance_m"] = distance_m

            except Exception as e:
                logger.debug(f"Failed to get property {prop_id}: {e}")
                continue

        # Map to standard names
        result = {}
        if "phh2o" in properties:
            result["ph"] = properties["phh2o"]
        if "soc" in properties:
            result["soc"] = properties["soc"]
        if "bdod" in properties:
            result["bdod"] = properties["bdod"]
        if "clay" in properties:
            result["clay"] = properties["clay"]
        if "sand" in properties:
            result["sand"] = properties["sand"]
        if "silt" in properties:
            result["silt"] = properties["silt"]
        if "nitrogen" in properties:
            result["nitrogen"] = properties["nitrogen"]
        if "distance_m" in properties:
            result["distance_m"] = properties["distance_m"]

        return result

    def _get_wcs_coverage(
        self, service: str, coverage_id: str, lat: float, lon: float
    ) -> bytes | None:
        """Get WCS coverage data with WCS 2.0.1 -> 1.0.0 fallback."""
        # Try WCS 2.0.1 first
        tiff_data = self._get_wcs_201(service, coverage_id, lat, lon)
        if tiff_data:
            return tiff_data

        # Fallback to WCS 1.0.0
        return self._get_wcs_100(service, coverage_id, lat, lon)

    def _get_wcs_201(
        self, service: str, coverage_id: str, lat: float, lon: float
    ) -> bytes | None:
        """Get coverage using WCS 2.0.1."""
        # Create 3x3 pixel window around point
        dlat, dlon = self._deg_window_for_pixels(lat, pixels=3)
        south, north = lat - dlat / 2, lat + dlat / 2
        west, east = lon - dlon / 2, lon + dlon / 2

        params = [
            ("SERVICE", "WCS"),
            ("VERSION", "2.0.1"),
            ("REQUEST", "GetCoverage"),
            ("COVERAGEID", coverage_id),
            ("FORMAT", "image/tiff"),
            ("SUBSET", f"lat({south},{north})"),
            ("SUBSET", f"long({west},{east})"),
            ("SUBSETTINGCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
            ("OUTPUTCRS", "http://www.opengis.net/def/crs/EPSG/0/4326"),
        ]

        url = self.wcs_base.format(service=service)
        response = self._session.get(url, params=params, timeout=self.timeout)

        if response.ok and response.headers.get("Content-Type", "").startswith(
            "image/tiff"
        ):
            return response.content

        return None

    def _get_wcs_100(
        self, service: str, coverage_id: str, lat: float, lon: float
    ) -> bytes | None:
        """Get coverage using WCS 1.0.0 (fallback)."""
        dlat, dlon = self._deg_window_for_pixels(lat, pixels=3)
        south, north = lat - dlat / 2, lat + dlat / 2
        west, east = lon - dlon / 2, lon + dlon / 2

        params = {
            "SERVICE": "WCS",
            "VERSION": "1.0.0",
            "REQUEST": "GetCoverage",
            "COVERAGE": coverage_id,
            "FORMAT": "GeoTIFF",
            "BBOX": f"{west},{south},{east},{north}",
            "CRS": "EPSG:4326",
            "RESPONSE_CRS": "EPSG:4326",
            "WIDTH": "3",
            "HEIGHT": "3",
        }

        url = self.wcs_base.format(service=service)
        response = self._session.get(url, params=params, timeout=self.timeout)

        if response.ok and response.headers.get("Content-Type", "").startswith(
            "image/tiff"
        ):
            return response.content

        return None

    def _extract_pixel_value(
        self, tiff_data: bytes, lat: float, lon: float
    ) -> float | None:
        """Extract pixel value from GeoTIFF at given coordinates."""
        try:
            with MemoryFile(tiff_data) as mem, mem.open() as dataset:
                row, col = dataset.index(lon, lat)
                row = int(np.clip(row, 0, dataset.height - 1))
                col = int(np.clip(col, 0, dataset.width - 1))

                arr = dataset.read(1)
                value = arr[row, col]

                # Check for no-data values
                if value in [-32768, 32767] or np.isnan(value):
                    return None

                return float(value)
        except Exception as e:
            logger.debug(f"Error extracting pixel value: {e}")
            return None

    def _calculate_pixel_distance(
        self, tiff_data: bytes, lat: float, lon: float
    ) -> float:
        """Calculate distance from requested point to pixel center."""
        try:
            with MemoryFile(tiff_data) as mem, mem.open() as dataset:
                row, col = dataset.index(lon, lat)
                row = int(np.clip(row, 0, dataset.height - 1))
                col = int(np.clip(col, 0, dataset.width - 1))

                pixel_lon, pixel_lat = dataset.xy(row, col, offset="center")
                return self._haversine_distance(
                    lat, lon, float(pixel_lat), float(pixel_lon)
                )
        except Exception:
            return 125.0  # Default for 250m resolution

    def _deg_window_for_pixels(
        self, lat: float, pixels: int = 3, pixel_m: float = 250.0
    ) -> tuple[float, float]:
        """Calculate degree window for pixel window."""
        dlat = (pixels * pixel_m) / 110574.0  # meters per degree latitude
        m_per_deg_lon = 111320.0 * max(0.0001, math.cos(math.radians(lat)))
        dlon = (pixels * pixel_m) / m_per_deg_lon
        return dlat, dlon

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000.0  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_completeness(self, wrb_data: dict, properties: dict) -> float:
        """Calculate data completeness score."""
        total_fields = 8  # wrb, ph, soc, bdod, sand, silt, clay, nitrogen
        found_fields = 0

        if wrb_data.get("classification"):
            found_fields += 1

        property_fields = ["ph", "soc", "bdod", "sand", "silt", "clay", "nitrogen"]
        for field in property_fields:
            if properties.get(field) is not None:
                found_fields += 1

        return found_fields / total_fields
