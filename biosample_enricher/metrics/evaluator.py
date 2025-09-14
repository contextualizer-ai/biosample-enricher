"""Coverage evaluator for biosample enrichment metrics.

Focuses on elevation and place name coverage, comparing before and after enrichment.
"""

from typing import Any

from biosample_enricher.elevation.classifier import CoordinateClassifier
from biosample_enricher.elevation.service import ElevationService
from biosample_enricher.forward_geocoding.service import ForwardGeocodingService
from biosample_enricher.land.service import LandService
from biosample_enricher.logging_config import get_logger
from biosample_enricher.marine.service import MarineService
from biosample_enricher.models import BiosampleLocation, ElevationRequest, ValueStatus
from biosample_enricher.osm_features.service import OSMFeaturesService
from biosample_enricher.reverse_geocoding.service import ReverseGeocodingService
from biosample_enricher.soil.service import SoilService
from biosample_enricher.weather.service import WeatherService

logger = get_logger(__name__)


class CoverageEvaluator:
    """Evaluates coverage improvement from enrichment."""

    def __init__(self) -> None:
        """Initialize evaluator with enrichment services."""
        self.elevation_service = ElevationService()
        self.geocoding_service = ReverseGeocodingService()
        self.forward_geocoding_service = ForwardGeocodingService()
        self.weather_service = WeatherService()
        self.marine_service = MarineService()
        self.soil_service = SoilService()
        self.land_service = LandService()
        self.osm_features_service = OSMFeaturesService()
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
            "forward_geocoding": self._evaluate_forward_geocoding(
                raw_doc, normalized_location, source
            ),
            "weather": self._evaluate_weather(raw_doc, normalized_location, source),
            "marine": self._evaluate_marine(raw_doc, normalized_location, source),
            "soil": self._evaluate_soil(raw_doc, normalized_location, source),
            "land": self._evaluate_land(raw_doc, normalized_location, source),
            "osm_features": self._evaluate_osm_features(
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
            "Alabama",
            "Alaska",
            "Arizona",
            "Arkansas",
            "California",
            "Colorado",
            "Connecticut",
            "Delaware",
            "Florida",
            "Georgia",
            "Hawaii",
            "Idaho",
            "Illinois",
            "Indiana",
            "Iowa",
            "Kansas",
            "Kentucky",
            "Louisiana",
            "Maine",
            "Maryland",
            "Massachusetts",
            "Michigan",
            "Minnesota",
            "Mississippi",
            "Missouri",
            "Montana",
            "Nebraska",
            "Nevada",
            "New Hampshire",
            "New Jersey",
            "New Mexico",
            "New York",
            "North Carolina",
            "North Dakota",
            "Ohio",
            "Oklahoma",
            "Oregon",
            "Pennsylvania",
            "Rhode Island",
            "South Carolina",
            "South Dakota",
            "Tennessee",
            "Texas",
            "Utah",
            "Vermont",
            "Virginia",
            "Washington",
            "West Virginia",
            "Wisconsin",
            "Wyoming",
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
                            components["state"] = parts[1]  # Second part is state
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

    def _evaluate_forward_geocoding(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate forward geocoding coverage (place names to coordinates).

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            Forward geocoding coverage metrics
        """
        logger.info(f"\n🌍 FORWARD GEOCODING ANALYSIS for {location.sample_id}")
        logger.info(f"Source: {source}")

        # Extract place name from raw document
        place_name = None
        if source == "nmdc":
            place_name_data = raw_doc.get("geo_loc_name")
            if place_name_data:
                if isinstance(place_name_data, str):
                    place_name = place_name_data
                elif isinstance(place_name_data, dict):
                    place_name = (
                        place_name_data.get("has_raw_value")
                        or place_name_data.get("name")
                        or str(place_name_data)
                    )
        elif source == "gold":
            place_name = (
                raw_doc.get("geographicLocation")
                or raw_doc.get("geoLocation")
                or raw_doc.get("sampleCollectionSite")
            )

        logger.info(f"📍 EXTRACTED PLACE NAME: {place_name}")

        # Check if we already have coordinates
        has_coordinates_before = (
            location.latitude is not None and location.longitude is not None
        )

        # Try forward geocoding enrichment if we have a place name but no coordinates
        has_coordinates_after = has_coordinates_before
        enriched_coordinates = None
        enrichment_error = None
        providers_used = []
        enrichment_data = {}

        if place_name and not has_coordinates_before:
            try:
                logger.info(f"🚀 CALLING FORWARD GEOCODING SERVICE for '{place_name}'")

                # Determine country hint from existing data
                country_hint = None
                if source == "gold":
                    country_hint = raw_doc.get("isoCountry")

                # Get coordinates from place name
                enrichment_data = (
                    self.forward_geocoding_service.get_coordinates_for_place(
                        place_name, country_hint=country_hint
                    )
                )

                if (
                    enrichment_data
                    and "latitude" in enrichment_data
                    and "longitude" in enrichment_data
                ):
                    logger.info("✅ FORWARD GEOCODING ENRICHMENT SUCCESSFUL")
                    has_coordinates_after = True
                    enriched_coordinates = {
                        "latitude": enrichment_data["latitude"],
                        "longitude": enrichment_data["longitude"],
                    }
                    providers_used = enrichment_data.get("providers_successful", [])

                    logger.info(
                        f"📈 Enriched coordinates: {enriched_coordinates['latitude']:.6f}, {enriched_coordinates['longitude']:.6f}"
                    )
                    logger.info(f"📈 Providers used: {', '.join(providers_used)}")
                else:
                    logger.warning("❌ FORWARD GEOCODING ENRICHMENT FAILED")
                    enrichment_error = (
                        enrichment_data.get("errors", ["No coordinates returned"])[0]
                        if enrichment_data
                        else "No enrichment data returned"
                    )

            except Exception as e:
                logger.error(f"❌ FORWARD GEOCODING ERROR: {e}")
                enrichment_error = str(e)
        elif not place_name:
            logger.info("⏭️  SKIPPING: No place name available")
            enrichment_error = "No place name provided"
        else:
            logger.info("⏭️  SKIPPING: Coordinates already available")
            enrichment_error = "Coordinates already present"

        # Calculate metrics
        before_count = 2 if has_coordinates_before else 0
        after_count = 2 if has_coordinates_after else 0
        improvement = after_count - before_count

        # Track additional enriched fields from forward geocoding
        additional_fields = [
            "country",
            "country_code",
            "state",
            "city",
            "formatted_address",
        ]
        additional_before = 0
        additional_after = 0

        # Count existing geographic fields
        for field in additional_fields:
            if self._has_geographic_field(raw_doc, field):
                additional_before += 1

        # Count enriched geographic fields
        additional_after = additional_before
        if enrichment_data:
            for field in additional_fields:
                if field in enrichment_data and field not in raw_doc:
                    additional_after += 1

        logger.info(
            f"📊 FORWARD GEOCODING BEFORE: coordinates={has_coordinates_before}, additional_fields={additional_before}"
        )
        logger.info(
            f"📊 FORWARD GEOCODING AFTER: coordinates={has_coordinates_after}, additional_fields={additional_after}"
        )
        logger.info(
            f"📈 COORDINATE IMPROVEMENT: {'+' if improvement > 0 else ''}{improvement}"
        )

        return {
            "before_has_coordinates": has_coordinates_before,
            "after_has_coordinates": has_coordinates_after,
            "coordinates_improved": improvement > 0,
            "enriched_coordinates": enriched_coordinates,
            "before_coordinate_count": before_count,
            "after_coordinate_count": after_count,
            "coordinate_improvement": improvement,
            "additional_fields_before": additional_before,
            "additional_fields_after": additional_after,
            "additional_fields_improvement": additional_after - additional_before,
            "place_name_input": place_name,
            "providers_used": providers_used,
            "enrichment_data": enrichment_data,
            "enrichment_error": enrichment_error,
        }

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

    def _evaluate_marine(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate marine coverage before and after enrichment.

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            Marine coverage metrics
        """
        logger.info(f"\n🌊 MARINE ANALYSIS for {location.sample_id}")
        logger.info(f"Source: {source}")

        # Define marine parameter fields for schema mapping
        marine_fields = {
            "sea_surface_temperature": [
                "temp",
                "sampleCollectionTemperature",
                "temperature",
            ],
            "bathymetry": ["tot_depth_water_col", "depthInMeters", "depth", "elev"],
            "chlorophyll_a": ["chlorophyll", "chl_a", "chlorophyll_a"],
            "salinity": ["salinity", "salinityConcentration"],
            "dissolved_oxygen": ["diss_oxygen", "oxygenConcentration", "oxygen"],
            "ph": ["ph", "pH"],
            "ocean_currents": ["current_u", "current_v", "ocean_velocity"],
            "wave_height": ["wave_height", "significant_wave_height"],
        }

        # Analyze before coverage
        before_coverage = {}
        for marine_param, field_names in marine_fields.items():
            has_field = False
            for field_name in field_names:
                if self._has_marine_field(raw_doc, field_name):
                    has_field = True
                    break
            before_coverage[marine_param] = has_field

        before_count = sum(before_coverage.values())
        logger.info(
            f"📊 MARINE BEFORE: {before_count}/{len(marine_fields)} fields present"
        )

        # Try marine enrichment if we have coordinates and collection date
        after_coverage = before_coverage.copy()  # Start with existing data
        enrichment_error = None
        providers_used = []
        data_quality = None

        if (
            location.latitude is not None
            and location.longitude is not None
            and location.collection_date is not None
        ):
            try:
                # Create biosample dict for marine service
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
                    f"🚀 CALLING MARINE SERVICE for {location.latitude}, {location.longitude} on {location.collection_date}"
                )

                # Get marine enrichment
                target_schema = "nmdc" if source.lower() == "nmdc" else "gold"
                marine_result = self.marine_service.get_marine_data_for_biosample(
                    biosample_dict, target_schema=target_schema
                )

                if marine_result.get("enrichment_success"):
                    logger.info("✅ MARINE ENRICHMENT SUCCESSFUL")
                    marine_data = marine_result["marine_result"]
                    providers_used = marine_data.successful_providers
                    data_quality = marine_data.overall_quality.value

                    # Check which marine parameters were enriched
                    for marine_param in marine_fields:
                        if (
                            hasattr(marine_data, marine_param)
                            and getattr(marine_data, marine_param) is not None
                        ):
                            after_coverage[marine_param] = True

                    logger.info(
                        f"📈 Marine providers used: {', '.join(providers_used)}"
                    )
                    logger.info(f"📈 Marine data quality: {data_quality}")
                else:
                    logger.warning("❌ MARINE ENRICHMENT FAILED")
                    enrichment_error = marine_result.get("error", "Unknown error")

            except Exception as e:
                logger.error(f"💥 MARINE SERVICE ERROR: {e}")
                enrichment_error = str(e)

        after_count = sum(after_coverage.values())
        improvement = after_count > before_count

        logger.info(
            f"📊 MARINE AFTER: {after_count}/{len(marine_fields)} fields present"
        )
        logger.info(f"📈 MARINE IMPROVED: {improvement}")

        return {
            "before": before_coverage,
            "after": after_coverage,
            "before_count": before_count,
            "after_count": after_count,
            "total_possible": len(marine_fields),
            "improved": improvement,
            "providers": providers_used,
            "error": enrichment_error,
            "data_quality": data_quality,
        }

    def _has_marine_field(self, biosample: dict[str, Any], field_name: str) -> bool:
        """Check if biosample has data for a specific marine field."""
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

    def _evaluate_soil(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate soil coverage before and after enrichment.

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            Soil coverage metrics
        """
        logger.info(f"\n🌱 SOIL ANALYSIS for {location.sample_id}")
        logger.info(f"Source: {source}")

        # Define soil parameter fields for schema mapping
        soil_fields = {
            "soil_type": ["soil_type", "soilType"],
            "soil_classification": ["soil_classification", "soilClassification"],
            "ph": ["ph", "pH", "soil_ph"],
            "texture": ["soil_texture_meth", "texture", "soilTexture"],
            "horizon": ["soil_horizon", "horizon", "soilHorizon"],
            "organic_carbon": ["org_carb", "soil_organic_carbon", "organicCarbon"],
            "total_nitrogen": ["tot_nitro", "total_nitrogen", "totalNitrogen"],
            "bulk_density": ["bulk_density", "soil_density", "bulkDensity"],
            "sand_percent": ["sand", "sand_percent", "sandPercent"],
            "silt_percent": ["silt", "silt_percent", "siltPercent"],
            "clay_percent": ["clay", "clay_percent", "clayPercent"],
            "cation_exchange": ["cec", "cation_exchange_capacity", "cationExchange"],
        }

        # Analyze before coverage
        before_coverage = {}
        for soil_param, field_names in soil_fields.items():
            has_field = False
            for field_name in field_names:
                if self._has_soil_field(raw_doc, field_name):
                    has_field = True
                    break
            before_coverage[soil_param] = has_field

        before_count = sum(before_coverage.values())
        logger.info(f"📊 SOIL BEFORE: {before_count}/{len(soil_fields)} fields present")

        # Try soil enrichment if we have coordinates
        after_coverage = before_coverage.copy()  # Start with existing data
        enrichment_error = None
        providers_used = []
        data_quality = None
        distance_m = None

        if location.latitude is not None and location.longitude is not None:
            try:
                logger.info(
                    f"🚀 CALLING SOIL SERVICE for {location.latitude}, {location.longitude}"
                )

                # Get soil enrichment
                soil_result = self.soil_service.enrich_location(
                    location.latitude, location.longitude
                )

                if soil_result.observations and soil_result.quality_score > 0.1:
                    logger.info("✅ SOIL ENRICHMENT SUCCESSFUL")
                    providers_used.append(soil_result.provider)
                    data_quality = soil_result.quality_score
                    distance_m = soil_result.distance_m

                    # Check which soil parameters were enriched
                    obs = soil_result.observations[0]  # Use first observation

                    # Map soil observations to coverage fields
                    if obs.classification_usda or obs.classification_wrb:
                        after_coverage["soil_type"] = True
                        after_coverage["soil_classification"] = True

                    if obs.ph_h2o is not None:
                        after_coverage["ph"] = True

                    if obs.texture_class:
                        after_coverage["texture"] = True

                    if obs.organic_carbon is not None:
                        after_coverage["organic_carbon"] = True

                    if obs.total_nitrogen is not None:
                        after_coverage["total_nitrogen"] = True

                    if obs.bulk_density is not None:
                        after_coverage["bulk_density"] = True

                    if obs.sand_percent is not None:
                        after_coverage["sand_percent"] = True

                    if obs.silt_percent is not None:
                        after_coverage["silt_percent"] = True

                    if obs.clay_percent is not None:
                        after_coverage["clay_percent"] = True

                    if obs.cation_exchange_capacity is not None:
                        after_coverage["cation_exchange"] = True

                    logger.info(f"📈 Soil provider used: {soil_result.provider}")
                    logger.info(f"📈 Soil data quality: {data_quality:.2f}")
                    if distance_m:
                        logger.info(f"📏 Soil measurement distance: {distance_m:.1f}m")
                else:
                    logger.warning("❌ SOIL ENRICHMENT FAILED - No observations")
                    enrichment_error = "No soil observations returned"

            except Exception as e:
                logger.error(f"💥 SOIL SERVICE ERROR: {e}")
                enrichment_error = str(e)

        after_count = sum(after_coverage.values())
        improvement = after_count > before_count

        logger.info(f"📊 SOIL AFTER: {after_count}/{len(soil_fields)} fields present")
        logger.info(f"📈 SOIL IMPROVED: {improvement}")

        return {
            "before": before_coverage,
            "after": after_coverage,
            "before_count": before_count,
            "after_count": after_count,
            "total_possible": len(soil_fields),
            "improved": improvement,
            "providers": providers_used,
            "error": enrichment_error,
            "data_quality": data_quality,
            "distance_m": distance_m,
        }

    def _has_soil_field(self, biosample: dict[str, Any], field_name: str) -> bool:
        """Check if biosample has data for a specific soil field."""
        if field_name not in biosample:
            return False

        value = biosample[field_name]

        # Handle NMDC QuantityValue format
        if isinstance(value, dict):
            if "has_numeric_value" in value and value["has_numeric_value"] is not None:
                return True
            if "has_raw_value" in value and value["has_raw_value"] is not None:
                return True
            if "term" in value and value["term"] is not None:
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

    def _evaluate_land(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate land cover and vegetation coverage before and after enrichment.

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            Land coverage metrics
        """
        logger.info(f"\n🌍 LAND ANALYSIS for {location.sample_id}")
        logger.info(f"Source: {source}")

        # Define land cover and vegetation parameter fields for schema mapping
        land_fields = {
            "current_vegetation": [
                "cur_vegetation",
                "current_vegetation",
                "vegetation",
            ],
            "land_cover_class": ["land_cover", "landCover", "land_use"],
            "ndvi": ["ndvi", "NDVI", "normalized_difference_vegetation_index"],
            "evi": ["evi", "EVI", "enhanced_vegetation_index"],
            "lai": ["lai", "LAI", "leaf_area_index"],
            "fpar": ["fpar", "FPAR", "fraction_photosynthetically_active_radiation"],
            "land_use": ["land_use", "landUse", "land_usage"],
            "habitat": ["habitat", "habitatDetails", "environmental_context"],
            "biome": ["biome", "env_broad_scale", "broad_scale_environmental_context"],
            "vegetation_type": ["vegetation_type", "vegetationType", "veg_type"],
        }

        # Analyze before coverage
        before_coverage = {}
        for land_param, field_names in land_fields.items():
            has_field = False
            for field_name in field_names:
                if self._has_land_field(raw_doc, field_name):
                    has_field = True
                    break
            before_coverage[land_param] = has_field

        before_count = sum(before_coverage.values())
        logger.info(f"📊 LAND BEFORE: {before_count}/{len(land_fields)} fields present")

        # Try land enrichment if we have coordinates
        after_coverage = before_coverage.copy()  # Start with existing data
        enrichment_error = None
        providers_used = []
        data_quality = None
        distance_m = None

        if location.latitude is not None and location.longitude is not None:
            try:
                logger.info(
                    f"🚀 CALLING LAND SERVICE for {location.latitude}, {location.longitude}"
                )

                # Get land enrichment
                land_result = self.land_service.enrich_location(
                    location.latitude, location.longitude
                )

                if (
                    land_result.land_cover or land_result.vegetation
                ) and land_result.overall_quality_score > 0.1:
                    logger.info("✅ LAND ENRICHMENT SUCCESSFUL")
                    providers_used = land_result.providers_successful
                    data_quality = land_result.overall_quality_score

                    # Check which land cover parameters were enriched
                    if land_result.land_cover:
                        after_coverage["land_cover_class"] = True
                        after_coverage["habitat"] = True

                        # Check for specific vegetation classification
                        for obs in land_result.land_cover:
                            if obs.class_label and any(
                                veg_term in obs.class_label.lower()
                                for veg_term in [
                                    "grass",
                                    "forest",
                                    "shrub",
                                    "crop",
                                    "wetland",
                                ]
                            ):
                                after_coverage["current_vegetation"] = True
                                after_coverage["vegetation_type"] = True

                    # Check which vegetation parameters were enriched
                    if land_result.vegetation:
                        for veg_obs in land_result.vegetation:
                            if veg_obs.ndvi is not None:
                                after_coverage["ndvi"] = True
                            if veg_obs.evi is not None:
                                after_coverage["evi"] = True
                            if veg_obs.lai is not None:
                                after_coverage["lai"] = True
                            if veg_obs.fpar is not None:
                                after_coverage["fpar"] = True

                        # Calculate average distance for vegetation observations
                        distances = [
                            obs.distance_m
                            for obs in land_result.vegetation
                            if obs.distance_m
                        ]
                        if distances:
                            distance_m = sum(distances) / len(distances)

                else:
                    logger.info("❌ LAND ENRICHMENT FAILED OR LOW QUALITY")
                    if land_result.errors:
                        enrichment_error = "; ".join(land_result.errors[:3])

            except Exception as e:
                logger.error(f"❌ LAND ENRICHMENT ERROR: {e}")
                enrichment_error = str(e)

        after_count = sum(after_coverage.values())
        improvement = after_count - before_count
        logger.info(
            f"📊 LAND AFTER: {after_count}/{len(land_fields)} fields present (+{improvement})"
        )

        return {
            "before_count": before_count,
            "after_count": after_count,
            "improvement": improvement,
            "before_coverage": before_coverage,
            "after_coverage": after_coverage,
            "providers_used": providers_used,
            "data_quality": data_quality,
            "distance_m": distance_m,
            "enrichment_error": enrichment_error,
        }

    def _has_land_field(self, biosample: dict[str, Any], field_name: str) -> bool:
        """Check if a land-related field has meaningful data."""
        if field_name not in biosample:
            return False

        value = biosample[field_name]

        # Handle NMDC QuantityValue format
        if isinstance(value, dict):
            if "has_numeric_value" in value and value["has_numeric_value"] is not None:
                return True
            if "has_raw_value" in value and value["has_raw_value"] is not None:
                return True
            if "term" in value and value["term"] is not None:
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

    def _has_geographic_field(self, biosample: dict[str, Any], field_name: str) -> bool:
        """Check if biosample has data for a specific geographic field."""
        if field_name not in biosample:
            return False

        value = biosample[field_name]

        # Handle NMDC TextValue format (for location names)
        if isinstance(value, dict):
            if "has_raw_value" in value and value["has_raw_value"]:
                return True
            if "name" in value and value["name"]:
                return True

        # Handle direct string values or lists
        elif (isinstance(value, str) and value.strip()) or (
            isinstance(value, list) and value
        ):
            return True

        return False

    def _evaluate_osm_features(
        self, raw_doc: dict[str, Any], location: BiosampleLocation, source: str
    ) -> dict[str, Any]:
        """Evaluate OSM geographic features coverage before and after enrichment.

        Args:
            raw_doc: Original document
            location: Normalized location
            source: Data source

        Returns:
            OSM features coverage metrics
        """
        logger.info(f"\\n🗺️  OSM FEATURES ANALYSIS for {location.sample_id}")
        logger.info(f"Source: {source}")

        # Check for existing geographic feature data in raw document
        feature_fields = {
            "natural_features": ["natural", "natural_feature", "environmental_context"],
            "water_features": ["waterway", "water_body", "water_feature"],
            "transport_features": ["highway", "railway", "transport", "road"],
            "buildings": ["building", "structure", "building_type"],
            "amenities": ["amenity", "facility", "amenities"],
            "land_use": ["land_use", "landuse", "land_cover"],
        }

        # Analyze before coverage
        before_coverage = {}
        for feature_type, field_names in feature_fields.items():
            has_field = False
            for field_name in field_names:
                if self._has_geographic_field(raw_doc, field_name):
                    has_field = True
                    break
            before_coverage[feature_type] = has_field

        before_count = sum(before_coverage.values())
        logger.info(
            f"📊 OSM FEATURES BEFORE: {before_count}/{len(feature_fields)} feature types present"
        )

        # Try OSM features enrichment if we have coordinates
        after_coverage = before_coverage.copy()  # Start with existing data
        enrichment_error = None
        features_found = 0
        categories_found = 0
        total_elements = 0
        nearest_features = {}

        if location.latitude is not None and location.longitude is not None:
            try:
                logger.info(
                    f"🚀 CALLING OSM FEATURES SERVICE for {location.latitude}, {location.longitude}"
                )

                # Get OSM features enrichment
                osm_result = self.osm_features_service.get_features_for_location(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    radius_m=1000,  # Default 1km radius
                    timeout_s=60,  # Shorter timeout for metrics
                )

                if osm_result and osm_result.success:
                    logger.info("✅ OSM FEATURES ENRICHMENT SUCCESSFUL")
                    features_found = osm_result.named_features_count
                    categories_found = osm_result.unnamed_categories_count
                    total_elements = osm_result.total_elements

                    # Update coverage based on found features
                    if osm_result.named_features:
                        # Categorize found features
                        for feature in osm_result.named_features:
                            category = feature.category.value
                            if category == "natural":
                                after_coverage["natural_features"] = True
                            elif category == "waterway":
                                after_coverage["water_features"] = True
                            elif category in ["highway", "railway"]:
                                after_coverage["transport_features"] = True
                            elif category == "building":
                                after_coverage["buildings"] = True
                            elif category == "amenity":
                                after_coverage["amenities"] = True
                            elif category == "landuse":
                                after_coverage["land_use"] = True

                        # Track nearest features by category (simplified approach)
                        nearest_natural = next(
                            (
                                f
                                for f in osm_result.named_features
                                if f.category.value == "natural"
                            ),
                            None,
                        )
                        if nearest_natural:
                            nearest_features["natural"] = {
                                "name": nearest_natural.name,
                                "distance_km": nearest_natural.distance_km,
                                "type": nearest_natural.subcategory,
                            }

                    # Check unnamed feature categories
                    if osm_result.unnamed_counts:
                        for unnamed_group in osm_result.unnamed_counts:
                            key = unnamed_group.key
                            if key == "natural" and unnamed_group.total_count > 0:
                                after_coverage["natural_features"] = True
                            elif key == "waterway" and unnamed_group.total_count > 0:
                                after_coverage["water_features"] = True
                            elif (
                                key in ["highway", "railway"]
                                and unnamed_group.total_count > 0
                            ):
                                after_coverage["transport_features"] = True
                            elif key == "building" and unnamed_group.total_count > 0:
                                after_coverage["buildings"] = True
                            elif key == "amenity" and unnamed_group.total_count > 0:
                                after_coverage["amenities"] = True
                            elif key == "landuse" and unnamed_group.total_count > 0:
                                after_coverage["land_use"] = True

                    logger.info(f"📈 OSM features found: {features_found} named")
                    logger.info(f"📈 OSM categories found: {categories_found}")

                else:
                    logger.warning("❌ OSM FEATURES ENRICHMENT FAILED")
                    enrichment_error = "No OSM features returned or query failed"

            except Exception as e:
                logger.error(f"💥 OSM FEATURES SERVICE ERROR: {e}")
                enrichment_error = str(e)

        after_count = sum(after_coverage.values())
        improvement = after_count > before_count

        logger.info(
            f"📊 OSM FEATURES AFTER: {after_count}/{len(feature_fields)} feature types present"
        )
        logger.info(f"📈 OSM FEATURES IMPROVED: {improvement}")

        return {
            "before": before_coverage,
            "after": after_coverage,
            "before_count": before_count,
            "after_count": after_count,
            "total_possible": len(feature_fields),
            "improved": improvement,
            "features_found": features_found,
            "categories_found": categories_found,
            "total_elements": total_elements,
            "nearest_features": nearest_features,
            "error": enrichment_error,
        }
