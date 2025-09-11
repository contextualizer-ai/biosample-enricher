"""Coverage evaluator for biosample enrichment metrics.

Focuses on elevation and place name coverage, comparing before and after enrichment.
"""

from typing import Any

from biosample_enricher.elevation.classifier import CoordinateClassifier
from biosample_enricher.elevation.service import ElevationService
from biosample_enricher.logging_config import get_logger
from biosample_enricher.models import BiosampleLocation, ElevationRequest, ValueStatus
from biosample_enricher.reverse_geocoding.service import ReverseGeocodingService

logger = get_logger(__name__)


class CoverageEvaluator:
    """Evaluates coverage improvement from enrichment."""

    def __init__(self) -> None:
        """Initialize evaluator with enrichment services."""
        self.elevation_service = ElevationService()
        self.geocoding_service = ReverseGeocodingService()
        self.classifier = CoordinateClassifier()

    def evaluate_sample(
        self,
        raw_doc: dict[str, Any],
        normalized_location: BiosampleLocation,
        source: str,
    ) -> dict[str, Any]:
        """Evaluate a single sample for coverage metrics.

        Args:
            raw_doc: Original raw document from database
            normalized_location: Normalized location from adapter
            source: 'nmdc' or 'gold'

        Returns:
            Evaluation results with before/after coverage
        """
        result = {
            "sample_id": normalized_location.sample_id,
            "source": source,
            "is_host_associated": normalized_location.is_host_associated,
            "sample_type": normalized_location.sample_type,
            "classification": self._classify_location(normalized_location),
            "elevation": self._evaluate_elevation(raw_doc, normalized_location, source),
            "place_name": self._evaluate_place_name(
                raw_doc, normalized_location, source
            ),
        }

        return result

    def _classify_location(self, location: BiosampleLocation) -> dict[str, Any]:
        """Classify the geographic location of the sample."""
        if location.latitude is None or location.longitude is None:
            return {
                "has_coordinates": False,
                "is_us_territory": None,
                "is_ocean": None,
                "region": None,
            }

        classification = self.classifier.classify(location.latitude, location.longitude)

        return {
            "has_coordinates": True,
            "is_us_territory": classification.is_us_territory,
            "is_ocean": classification.is_land is False
            if classification.is_land is not None
            else None,
            "region": classification.region,
            "coordinate_precision": location.coordinate_precision,
        }

    def _evaluate_elevation(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate elevation coverage before and after enrichment.

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            Elevation coverage metrics
        """
        logger.info(f"\n🔍 ELEVATION ANALYSIS for {location.sample_id}")
        logger.info(f"Raw document elevation fields: elev={raw_doc.get('elev')}, elevation={raw_doc.get('elevation')}")
        logger.info(f"Normalized location coordinates: lat={location.latitude}, lon={location.longitude}")
        logger.info(f"Source: {source}")
        
        # Check original elevation data
        before_value = None
        if source == "nmdc":
            before_value = raw_doc.get("elev") or raw_doc.get("elevation")
        elif source == "gold":
            before_value = (
                raw_doc.get("elevation")
                or raw_doc.get("altitudeMeters")
                or raw_doc.get("elevationMeters")
            )

        has_before = before_value is not None and before_value != ""
        logger.info(f"📊 ELEVATION BEFORE: value={before_value}, has_before={has_before}")

        # Try enrichment if we have coordinates
        after_value = None
        enrichment_error = None
        provider_used = None

        if location.latitude is not None and location.longitude is not None:
            try:
                # Create elevation request
                request = ElevationRequest(
                    latitude=location.latitude,
                    longitude=location.longitude,
                )

                # Get elevation from service
                logger.info(f"🚀 CALLING ELEVATION SERVICE for {location.latitude}, {location.longitude}")
                observations = self.elevation_service.get_elevation(request)
                logger.info(f"📨 ELEVATION RESPONSE: {len(observations)} observations")

                # Find best observation
                for i, obs in enumerate(observations):
                    logger.info(f"🔬 OBSERVATION {i+1}: status={obs.value_status}, value={obs.value_numeric}, provider={obs.provider.name if obs.provider else None}")
                    if obs.value_status == ValueStatus.OK and obs.value_numeric is not None:
                        after_value = obs.value_numeric
                        provider_used = obs.provider.name if obs.provider else None
                        logger.info(f"✅ SELECTED OBSERVATION: value={after_value}, provider={provider_used}")
                        break

                if after_value is None and observations:
                    # Capture error if no successful observation
                    for obs in observations:
                        if obs.error_message:
                            enrichment_error = obs.error_message
                            break

            except Exception as e:
                logger.debug(f"Elevation enrichment failed: {e}")
                enrichment_error = str(e)

        has_after = after_value is not None

        result = {
            "before": has_before,
            "before_value": float(before_value) if before_value else None,
            "after": has_after,
            "after_value": float(after_value) if after_value else None,
            "improved": has_after and not has_before,
            "provider": provider_used,
            "error": enrichment_error,
        }
        logger.info(f"📋 ELEVATION FINAL RESULT: {result}")
        return result

    def _evaluate_place_name(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate place name coverage before and after enrichment.

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            Place name coverage metrics
        """
        logger.info(f"\n🏷️  PLACE NAME ANALYSIS for {location.sample_id}")
        logger.info(f"Source: {source}")
        
        # Extract original place name
        before_value = None
        if source == "nmdc":
            before_value = raw_doc.get("geo_loc_name")
        elif source == "gold":
            before_value = (
                raw_doc.get("geoLocation")
                or raw_doc.get("geo_loc_name")
                or raw_doc.get("geographicLocation")
            )

        logger.info(f"📍 RAW PLACE NAME DATA: {before_value}")
        
        # Parse original place name into components
        # Handle both string values and dict values (NMDC might use complex structures)
        geo_loc_text = None
        if before_value:
            if isinstance(before_value, str):
                geo_loc_text = before_value
                logger.info(f"✅ String format: {geo_loc_text}")
            elif isinstance(before_value, dict):
                # Extract from dict structure, similar to ENVO terms
                geo_loc_text = before_value.get("has_raw_value") or before_value.get("name") or str(before_value)
                logger.info(f"🔧 Dict format converted to: {geo_loc_text}")
            else:
                geo_loc_text = str(before_value)
                logger.info(f"🔄 Other format converted to: {geo_loc_text}")
        
        before_components = (
            self._parse_geo_loc_name(geo_loc_text) if geo_loc_text else {}
        )
        logger.info(f"🧩 PARSED BEFORE COMPONENTS: {before_components}")
        has_before = len(before_components) > 0

        # Try reverse geocoding enrichment
        after_components = {}
        enrichment_error = None
        providers_used = []

        if location.latitude is not None and location.longitude is not None:
            try:
                logger.info(f"🌐 CALLING REVERSE GEOCODING for {location.latitude}, {location.longitude}")
                # Get reverse geocoding results from multiple providers
                results = self.geocoding_service.reverse_geocode_multiple(
                    location.latitude, location.longitude, providers=["osm", "google"]
                )
                logger.info(f"📨 REVERSE GEOCODING RESPONSE: {len(results)} provider results")

                # Merge results from all providers
                for provider_name, result in results.items():
                    if result.status == "OK" and result.locations:
                        providers_used.append(provider_name)

                        # Extract components from the best match
                        best_location = result.get_best_match()
                        if best_location:
                            # Extract and flatten components
                            if (
                                best_location.country
                                and "country" not in after_components
                            ):
                                after_components["country"] = best_location.country

                            # Look for state/administrative components
                            for component in best_location.components:
                                if (
                                    component.type == "administrative_area_level_1"
                                    and "state" not in after_components
                                    and component.long_name
                                ):
                                    after_components["state"] = component.long_name
                                elif (
                                    component.type == "locality"
                                    and "locality" not in after_components
                                    and component.long_name
                                ):
                                    after_components["locality"] = component.long_name

                    else:
                        if result.error_message and not enrichment_error:
                            enrichment_error = result.error_message

            except Exception as e:
                logger.debug(f"Reverse geocoding failed: {e}")
                enrichment_error = str(e)

        # Create flattened representations for comparison
        before_flat = self._create_geo_loc_name(before_components)
        after_flat = self._create_geo_loc_name(after_components)

        has_after = len(after_components) > 0

        # Apply additive-only enrichment: preserve original components, only add missing ones
        final_components = before_components.copy()
        for component_type in ["country", "state", "locality"]:
            if component_type not in final_components and component_type in after_components:
                final_components[component_type] = after_components[component_type]
                logger.info(f"🎯 ADDITIVE ENRICHMENT: Added missing {component_type}: {after_components[component_type]}")
        
        # Detailed component-level comparison
        component_coverage = {
            "country": {
                "before": before_components.get("country") is not None,
                "after": final_components.get("country") is not None,
            },
            "state": {
                "before": before_components.get("state") is not None,
                "after": final_components.get("state") is not None,
            },
            "locality": {
                "before": before_components.get("locality") is not None,
                "after": final_components.get("locality") is not None,
            },
        }

        # Calculate final metrics using additive-only approach
        final_flat = self._create_geo_loc_name(final_components)
        has_final = len(final_components) > 0
        
        return {
            "before": has_before,
            "before_value": before_value,
            "before_components": before_components,
            "before_flat": before_flat,
            "after": has_final,
            "after_components": final_components,
            "after_flat": final_flat,
            "improved": has_final and not has_before,
            "component_coverage": component_coverage,
            "providers": providers_used,
            "error": enrichment_error,
        }

    def _parse_geo_loc_name(self, geo_loc_name: str) -> dict[str, str]:
        """Parse geo_loc_name string into components.

        Format: "Country or Sea: State/Region, Locality/Site"
        Examples:
        - "USA: California, San Francisco Bay"
        - "Pacific Ocean: North Pacific"
        - "USA: Wisconsin, Lake Mendota"

        Args:
            geo_loc_name: The geo_loc_name string

        Returns:
            Dictionary with parsed components
        """
        components: dict[str, str] = {}

        if not geo_loc_name:
            return components

        # Split by colon first (country : rest)
        if ":" in geo_loc_name:
            country_part, rest = geo_loc_name.split(":", 1)
            components["country"] = country_part.strip()

            # Split rest by comma (state, locality)
            if "," in rest:
                parts = [p.strip() for p in rest.split(",")]
                if parts[0]:
                    components["state"] = parts[0]
                if len(parts) > 1 and parts[1]:
                    components["locality"] = parts[1]
            else:
                # Just state/region, no locality
                rest = rest.strip()
                if rest:
                    components["state"] = rest
        else:
            # No colon, might just be country or location name
            geo_loc_name = geo_loc_name.strip()
            if geo_loc_name:
                # Try to guess if it's a country or location
                if geo_loc_name.upper() in ["USA", "CANADA", "MEXICO"]:
                    components["country"] = geo_loc_name
                else:
                    components["locality"] = geo_loc_name

        return components

    def _create_geo_loc_name(self, components: dict[str, str]) -> str:
        """Create geo_loc_name string from components.

        Args:
            components: Dictionary with country, state, locality

        Returns:
            Formatted geo_loc_name string
        """
        if not components:
            return ""

        # Handle ocean/water body special case
        if "ocean" in components:
            base = components["ocean"]
            if "water_body" in components:
                return f"{base}: {components['water_body']}"
            return base

        # Standard format: "Country: State, Locality"
        parts = []

        if "country" in components:
            country = components["country"]
            sub_parts = []

            if "state" in components:
                sub_parts.append(components["state"])
            if "locality" in components:
                sub_parts.append(components["locality"])

            if sub_parts:
                return f"{country}: {', '.join(sub_parts)}"
            else:
                return country
        else:
            # No country, just concatenate what we have
            if "state" in components:
                parts.append(components["state"])
            if "locality" in components:
                parts.append(components["locality"])

            return ", ".join(parts) if parts else ""

    def evaluate_batch(
        self, samples: list[tuple[dict[str, Any], BiosampleLocation]], source: str
    ) -> list[dict[str, Any]]:
        """Evaluate a batch of samples.

        Args:
            samples: List of (raw_doc, normalized_location) tuples
            source: Data source ('nmdc' or 'gold')

        Returns:
            List of evaluation results
        """
        results = []

        for i, (raw_doc, location) in enumerate(samples):
            if i % 10 == 0:
                logger.info(f"Evaluating sample {i + 1}/{len(samples)} from {source}")

            try:
                result = self.evaluate_sample(raw_doc, location, source)
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating sample {location.sample_id}: {e}")
                # Add minimal result for failed evaluation
                results.append(
                    {"sample_id": location.sample_id, "source": source, "error": str(e)}
                )

        return results
