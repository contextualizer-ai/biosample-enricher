"""USDA NRCS Soil Data Access (SDA) provider for US soil taxonomy."""

import json

from biosample_enricher.http_cache import get_session
from biosample_enricher.logging_config import get_logger
from biosample_enricher.soil.models import SoilObservation, SoilResult
from biosample_enricher.soil.providers.base import SoilProviderBase

logger = get_logger(__name__)


class USDANRCSProvider(SoilProviderBase):
    """USDA NRCS Soil Data Access provider for US soil taxonomy.

    Provides high-quality USDA Soil Taxonomy classification for locations
    within the continental United States and territories.

    API Documentation: https://sdmdataaccess.sc.egov.usda.gov/
    """

    def __init__(self, timeout: int = 30):
        self.base_url = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
        self.timeout = timeout
        self._session = get_session()

    @property
    def name(self) -> str:
        return "USDA NRCS Soil Data Access"

    @property
    def coverage_description(self) -> str:
        return "Continental United States and territories - USDA Soil Taxonomy"

    def is_available(self) -> bool:
        """Check if USDA SDA is available."""
        try:
            # Simple ping query to check service availability
            test_query = {"query": "SELECT TOP 1 mukey FROM mapunit"}
            response = self._session.post(
                self.base_url,
                data={"FORMAT": "JSON", "QUERY": json.dumps(test_query)},
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_soil_data(
        self, latitude: float, longitude: float, depth_cm: str | None = "0-5cm"
    ) -> SoilResult:
        """Get USDA soil taxonomy data for a location.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            depth_cm: Depth interval (ignored - SDA provides full profile)

        Returns:
            SoilResult with USDA soil taxonomy classification
        """
        _ = depth_cm  # Unused for now
        self.validate_coordinates(latitude, longitude)

        try:
            # Get map unit key (mukey) for the location
            mukey = self._get_mukey(latitude, longitude)
            if not mukey:
                return SoilResult(
                    latitude=latitude,
                    longitude=longitude,
                    distance_m=0.0,
                    observations=[],
                    quality_score=0.0,
                    provider=self.name,
                    errors=["No soil map unit found at this location"],
                )

            # Get soil components and taxonomy for this map unit
            soil_components = self._get_soil_components(mukey)
            if not soil_components:
                return SoilResult(
                    latitude=latitude,
                    longitude=longitude,
                    distance_m=0.0,
                    observations=[],
                    quality_score=0.0,
                    provider=self.name,
                    errors=["No soil component data found for this map unit"],
                )

            # Convert to soil observations
            observations = []
            for component in soil_components:
                obs = self._component_to_observation(component)
                if obs:
                    observations.append(obs)

            # Calculate quality score
            quality_score = self._calculate_usda_quality(
                soil_components, latitude, longitude
            )

            logger.info(
                f"Retrieved USDA soil data for ({latitude}, {longitude}): {len(observations)} components"
            )

            return SoilResult(
                latitude=latitude,
                longitude=longitude,
                distance_m=0.0,
                observations=observations,
                quality_score=quality_score,
                provider=self.name,
            )

        except Exception as e:
            logger.error(f"Error retrieving USDA soil data: {e}")
            return SoilResult(
                latitude=latitude,
                longitude=longitude,
                distance_m=0.0,
                observations=[],
                quality_score=0.0,
                provider=self.name,
                errors=[str(e)],
            )

    def _get_mukey(self, latitude: float, longitude: float) -> str | None:
        """Get map unit key for a geographic location."""
        # Create WKT point geometry
        wkt_point = f"POINT({longitude} {latitude})"

        # Query to get mukey from spatial intersection
        query = {
            "query": f"""
                SELECT TOP 1 mukey
                FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt_point}')
                AS mukeys
            """
        }

        logger.debug(f"Querying USDA SDA for mukey at ({latitude}, {longitude})")

        response = self._session.post(
            self.base_url,
            data={"FORMAT": "JSON", "QUERY": json.dumps(query)},
            timeout=self.timeout,
        )

        if not response.ok:
            logger.warning(f"USDA SDA mukey query failed: {response.status_code}")
            return None

        try:
            data = response.json()
            if "Table" in data and data["Table"]:
                # Response format: {"Table": [["3056505"]]}
                mukey = data["Table"][0][0]
                logger.debug(f"Found mukey: {mukey}")
                return str(mukey)
            else:
                logger.debug("No mukey found in response")
                return None
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"Error parsing mukey response: {e}")
            return None

    def _get_soil_components(self, mukey: str) -> list[dict]:
        """Get soil components and taxonomy for a map unit."""
        # Query to get component data with soil taxonomy
        query = {
            "query": f"""
                SELECT
                    c.compname,
                    c.comppct_r,
                    c.majcompflag,
                    c.taxorder,
                    c.taxsubgrp,
                    c.taxgrtgrp,
                    c.taxsuborder,
                    c.taxpartsize,
                    c.taxceactcl,
                    c.taxreaction,
                    c.taxtempcl,
                    c.taxmoistscl,
                    c.taxtempregime,
                    c.soilslippot,
                    c.frostact
                FROM component c
                WHERE c.mukey = '{mukey}'
                    AND c.compkind = 'Series'
                ORDER BY c.comppct_r DESC
            """
        }

        logger.debug(f"Querying soil components for mukey: {mukey}")

        response = self._session.post(
            self.base_url,
            data={"FORMAT": "JSON", "QUERY": json.dumps(query)},
            timeout=self.timeout,
        )

        if not response.ok:
            logger.warning(f"USDA SDA components query failed: {response.status_code}")
            return []

        try:
            data = response.json()
            if "Table" not in data or not data["Table"]:
                logger.debug("No component data found")
                return []

            # Parse component data
            components = []
            column_names = [
                "compname",
                "comppct_r",
                "majcompflag",
                "taxorder",
                "taxsubgrp",
                "taxgrtgrp",
                "taxsuborder",
                "taxpartsize",
                "taxceactcl",
                "taxreaction",
                "taxtempcl",
                "taxmoistscl",
                "taxtempregime",
                "soilslippot",
                "frostact",
            ]

            for row in data["Table"]:
                component = {}
                for i, value in enumerate(row):
                    if i < len(column_names):
                        component[column_names[i]] = value
                components.append(component)

            logger.debug(f"Found {len(components)} soil components")
            return components

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error parsing components response: {e}")
            return []

    def _component_to_observation(self, component: dict) -> SoilObservation | None:
        """Convert a soil component to a SoilObservation."""
        try:
            # Build USDA taxonomy classification
            taxonomy_parts = []

            # Add taxonomic levels in hierarchical order
            if component.get("taxorder"):
                taxonomy_parts.append(component["taxorder"])
            if component.get("taxsuborder"):
                taxonomy_parts.append(component["taxsuborder"])
            if component.get("taxgrtgrp"):
                taxonomy_parts.append(component["taxgrtgrp"])
            if component.get("taxsubgrp"):
                taxonomy_parts.append(component["taxsubgrp"])

            if not taxonomy_parts:
                # Fallback to component name if no taxonomy
                if component.get("compname"):
                    classification = component["compname"]
                else:
                    return None
            else:
                classification = " > ".join(taxonomy_parts)

            # Calculate confidence from component percentage
            confidence = None
            if component.get("comppct_r"):
                # Convert percentage to confidence (0-1 scale)
                confidence = min(1.0, float(component["comppct_r"]) / 100.0)

            # Create observation
            return SoilObservation(
                classification_usda=classification,
                classification_wrb=None,
                confidence_usda=confidence,
                confidence_wrb=None,
                ph_h2o=None,
                organic_carbon=None,
                bulk_density=None,
                sand_percent=None,
                silt_percent=None,
                clay_percent=None,
                texture_class=None,
                total_nitrogen=None,
                available_phosphorus=None,
                cation_exchange_capacity=None,
                depth_cm="0-200cm",  # USDA represents full soil profile
                measurement_method="USDA NRCS Soil Data Access",
            )

        except Exception as e:
            logger.warning(f"Error converting component to observation: {e}")
            return None

    def _calculate_usda_quality(
        self, components: list[dict], latitude: float, longitude: float
    ) -> float:
        """Calculate quality score for USDA data."""
        _ = latitude, longitude  # Unused for now
        if not components:
            return 0.0

        # Base quality score
        quality = 0.8  # USDA data is generally high quality

        # Boost for major components
        has_major = any(comp.get("majcompflag") == "Yes" for comp in components)
        if has_major:
            quality += 0.1

        # Boost for detailed taxonomy
        detailed_taxonomy = any(comp.get("taxsubgrp") for comp in components)
        if detailed_taxonomy:
            quality += 0.1

        # Data completeness boost
        total_coverage = sum(float(comp.get("comppct_r", 0)) for comp in components)
        if total_coverage >= 80:  # Good map unit coverage
            quality += 0.05

        return min(1.0, quality)
