"""Coverage evaluator for biosample enrichment metrics.

Focuses on elevation and place name coverage, comparing before and after enrichment.
"""

from typing import Any

from biosample_enricher.elevation.classifier import CoordinateClassifier
from biosample_enricher.elevation.service import ElevationService
from biosample_enricher.logging_config import get_logger
from biosample_enricher.models import BiosampleLocation, ElevationRequest, ValueStatus
from biosample_enricher.reverse_geocoding.service import ReverseGeocodingService
from biosample_enricher.weather.service import WeatherService

logger = get_logger(__name__)


class CoverageEvaluator:
    """Evaluates coverage improvement from enrichment."""

    def __init__(self) -> None:
        """Initialize evaluator with enrichment services."""
        self.elevation_service = ElevationService()
        self.geocoding_service = ReverseGeocodingService()
        self.weather_service = WeatherService()
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
            "weather": self._evaluate_weather(raw_doc, normalized_location, source),
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
        logger.info(
            f"Raw document elevation fields: elev={raw_doc.get('elev')}, elevation={raw_doc.get('elevation')}"
        )
        logger.info(
            f"Normalized location coordinates: lat={location.latitude}, lon={location.longitude}"
        )
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
        logger.info(
            f"📊 ELEVATION BEFORE: value={before_value}, has_before={has_before}"
        )

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
                logger.info(
                    f"🚀 CALLING ELEVATION SERVICE for {location.latitude}, {location.longitude}"
                )
                observations = self.elevation_service.get_elevation(request)
                logger.info(f"📨 ELEVATION RESPONSE: {len(observations)} observations")

                # Find best observation
                for i, obs in enumerate(observations):
                    logger.info(
                        f"🔬 OBSERVATION {i + 1}: status={obs.value_status}, value={obs.value_numeric}, provider={obs.provider.name if obs.provider else None}"
                    )
                    if (
                        obs.value_status == ValueStatus.OK
                        and obs.value_numeric is not None
                    ):
                        after_value = obs.value_numeric
                        provider_used = obs.provider.name if obs.provider else None
                        logger.info(
                            f"✅ SELECTED OBSERVATION: value={after_value}, provider={provider_used}"
                        )
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
                geo_loc_text = (
                    before_value.get("has_raw_value")
                    or before_value.get("name")
                    or str(before_value)
                )
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
                logger.info(
                    f"🌐 CALLING REVERSE GEOCODING for {location.latitude}, {location.longitude}"
                )
                # Get reverse geocoding results from multiple providers
                results = self.geocoding_service.reverse_geocode_multiple(
                    location.latitude, location.longitude, providers=["osm", "google"]
                )
                logger.info(
                    f"📨 REVERSE GEOCODING RESPONSE: {len(results)} provider results"
                )

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

        # Apply additive-only enrichment: preserve original components, only add missing ones
        final_components = before_components.copy()
        for component_type in ["country", "state", "locality"]:
            if (
                component_type not in final_components
                and component_type in after_components
            ):
                final_components[component_type] = after_components[component_type]
                logger.info(
                    f"🎯 ADDITIVE ENRICHMENT: Added missing {component_type}: {after_components[component_type]}"
                )

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

        Handles multiple formats:
        - "USA: California, San Francisco Bay" (state, locality)
        - "USA: Central City, Nebraska" (locality, state) 
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

        # US state names for smart ordering detection
        us_states = {
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
            "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
            "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", 
            "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
            "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
            "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
            "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
        }

        # Split by colon first (country : rest)
        if ":" in geo_loc_name:
            country_part, rest = geo_loc_name.split(":", 1)
            components["country"] = country_part.strip()

            # Split rest by comma
            if "," in rest:
                parts = [p.strip() for p in rest.split(",")]
                if len(parts) >= 2 and parts[0] and parts[1]:
                    # Smart ordering detection for US addresses
                    if components["country"].upper() == "USA":
                        # Check if second part is a US state (common GOLD pattern: "City, State")
                        if parts[1] in us_states:
                            components["locality"] = parts[0]  # First part is city
                            components["state"] = parts[1]    # Second part is state
                        else:
                            # Default NMDC pattern: "State, City"  
                            components["state"] = parts[0]
                            components["locality"] = parts[1]
                    else:
                        # Non-US: assume first is region/state, second is locality
                        components["state"] = parts[0]
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

    def _evaluate_weather(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate weather coverage before and after enrichment.

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            Weather coverage metrics
        """
        logger.info(f"\n🌤️  WEATHER ANALYSIS for {location.sample_id}")
        logger.info(f"Source: {source}")

        # Check for existing weather data in raw document
        weather_fields = {
            "temperature": ["temp", "avg_temp", "sampleCollectionTemperature"],
            "wind_speed": ["wind_speed"],
            "wind_direction": ["wind_direction"],
            "humidity": ["humidity", "abs_air_humidity"],
            "solar_radiation": ["solar_irradiance", "photon_flux"],
            "precipitation": ["precipitation"],
            "pressure": ["pressure"],
            "chlorophyll": ["chlorophyll", "chl_a", "chlorophyll_a"],
        }

        # Analyze before coverage
        before_coverage = {}
        for weather_param, field_names in weather_fields.items():
            has_field = False
            for field_name in field_names:
                if self._has_weather_field(raw_doc, field_name):
                    has_field = True
                    break
            before_coverage[weather_param] = has_field

        before_count = sum(before_coverage.values())
        logger.info(
            f"📊 WEATHER BEFORE: {before_count}/{len(weather_fields)} fields present"
        )

        # Try weather enrichment if we have coordinates and collection date
        after_coverage = before_coverage.copy()  # Start with existing data
        enrichment_error = None
        providers_used = []
        measurement_distance = None

        if (
            location.latitude is not None
            and location.longitude is not None
            and location.collection_date is not None
        ):
            try:
                # Create biosample dict for weather service
                biosample_dict = {
                    "id": location.sample_id,
                    "lat_lon": {
                        "latitude": location.latitude,
                        "longitude": location.longitude,
                    },
                    "collection_date": {
                        "has_raw_value": location.collection_date.strftime("%Y-%m-%d")
                        if hasattr(location.collection_date, "strftime")
                        else str(location.collection_date)
                    },
                }

                logger.info(
                    f"🚀 CALLING WEATHER SERVICE for {location.latitude}, {location.longitude} on {location.collection_date}"
                )

                # Get weather enrichment
                target_schema = "nmdc" if source.lower() == "nmdc" else "gold"
                weather_result = self.weather_service.get_weather_for_biosample(
                    biosample_dict, target_schema=target_schema
                )

                if weather_result.get("enrichment_success"):
                    logger.info("✅ WEATHER ENRICHMENT SUCCESSFUL")
                    weather_data = weather_result["weather_result"]
                    providers_used = weather_data.successful_providers

                    # Calculate distance between requested and measurement location
                    measurement_distance = self._calculate_weather_distance(
                        location.latitude, location.longitude, weather_data
                    )

                    # Check which weather parameters were enriched
                    for weather_param in weather_fields:
                        if (
                            hasattr(weather_data, weather_param)
                            and getattr(weather_data, weather_param) is not None
                        ):
                            after_coverage[weather_param] = True

                    logger.info(
                        f"📈 Weather providers used: {', '.join(providers_used)}"
                    )
                    logger.info(
                        f"📏 Weather measurement distance: {measurement_distance:.1f} km"
                    )
                else:
                    logger.warning("❌ WEATHER ENRICHMENT FAILED")
                    enrichment_error = weather_result.get("error", "Unknown error")

            except Exception as e:
                logger.error(f"💥 WEATHER SERVICE ERROR: {e}")
                enrichment_error = str(e)

        after_count = sum(after_coverage.values())
        improvement = after_count > before_count

        logger.info(
            f"📊 WEATHER AFTER: {after_count}/{len(weather_fields)} fields present"
        )
        logger.info(f"📈 WEATHER IMPROVED: {improvement}")

        return {
            "before": before_coverage,
            "after": after_coverage,
            "before_count": before_count,
            "after_count": after_count,
            "total_possible": len(weather_fields),
            "improved": improvement,
            "providers": providers_used,
            "error": enrichment_error,
            "measurement_distance_km": measurement_distance,
        }

    def _has_weather_field(self, biosample: dict[str, Any], field_name: str) -> bool:
        """Check if biosample has data for a specific weather field."""
        if field_name not in biosample:
            return False

        value = biosample[field_name]

        # Handle NMDC QuantityValue format
        if isinstance(value, dict):
            if "has_numeric_value" in value and value["has_numeric_value"] is not None:
                return True
            if "has_raw_value" in value and value["has_raw_value"] is not None:
                return True

        # Handle direct numeric values or non-empty strings
        elif (
            isinstance(value, int | float)
            and value is not None
            or isinstance(value, str)
            and value.strip()
        ):
            return True

        return False

    def _calculate_weather_distance(
        self, request_lat: float, request_lon: float, weather_data: Any
    ) -> float:
        """
        Calculate distance between requested location and weather measurement location.

        Args:
            request_lat: Biosample latitude
            request_lon: Biosample longitude
            weather_data: WeatherResult object with location info

        Returns:
            Distance in kilometers
        """
        try:
            # Get measurement location from weather data
            measurement_lat = weather_data.location.get("lat", request_lat)
            measurement_lon = weather_data.location.get("lon", request_lon)

            # Calculate haversine distance
            import math

            # Convert to radians
            lat1, lon1, lat2, lon2 = map(
                math.radians,
                [request_lat, request_lon, measurement_lat, measurement_lon],
            )

            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            )
            c = 2 * math.asin(math.sqrt(a))

            # Earth radius in kilometers
            earth_radius_km = 6371.0
            distance_km = earth_radius_km * c

            return distance_km

        except Exception:
            # If distance calculation fails, return 0 (same location assumed)
            return 0.0

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
