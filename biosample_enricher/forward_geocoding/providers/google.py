"""Google forward geocoding provider using Google Maps Geocoding API."""

import os
import time
from typing import Any

from biosample_enricher.forward_geocoding.models import (
    BoundingBox,
    ForwardGeocodeFetchResult,
    ForwardGeocodeLocation,
    ForwardGeocodeProvider,
    ForwardGeocodeResult,
    GeometryType,
    LocationType,
)
from biosample_enricher.forward_geocoding.providers.base import ForwardGeocodingProvider
from biosample_enricher.http_cache import get_session
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class GoogleForwardGeocodingProvider(ForwardGeocodingProvider):
    """
    Google Geocoding (Forward) - Google Maps database

    Technical Characteristics:
        API Type: REST
        Endpoint: https://maps.googleapis.com/maps/api/geocode/json
        Authentication: api_key_required
        API Key: GOOGLE_MAIN_API_KEY
        Coverage: Global
        Resolution: Address-level precision

    Reliability:
        Stability: HIGH
        Data Quality: high
        Uptime: Excellent

    Cost:
        Model: paid
        Free Tier: No
        Quotas: Based on billing

    Strengths:
        ✓ High accuracy
        ✓ Global coverage
        ✓ Excellent address parsing
        ✓ Robust error handling

    Weaknesses:
        ✗ Requires paid API key
        ✗ Cost per request

    Best For:
        • Production with budget
        • High accuracy needs

    Not Suitable For:
        • High-volume without budget

    Complements:
        • OSM Nominatim (free fallback)

    NMDC Integration:
        Schema Slots: lat_lon
        Role: primary_if_key_available
        Excellent For: global

    See Also:
        Full comparison: config/provider_metadata.yaml
        API: https://maps.googleapis.com/maps/api/geocode/json
    """

    def __init__(self, api_key: str | None = None):
        """Initialize Google provider."""
        self.api_key = api_key or os.getenv("GOOGLE_MAIN_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required")

        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self._session = get_session()

    @property
    def name(self) -> str:
        return "Google Maps"

    @property
    def attribution(self) -> str:
        return "Powered by Google"

    def is_available(self) -> bool:
        """Check if Google API is available."""
        if not self.api_key:
            return False

        try:
            # Simple test request with a place name
            response = self._session.get(
                self.base_url,
                params={"address": "New York", "key": self.api_key},
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("status") in ["OK", "ZERO_RESULTS"]
            return False

        except Exception:
            return False

    def search(
        self,
        query: str,
        *,
        _read_from_cache: bool = True,
        _write_to_cache: bool = True,
        timeout_s: float = 30.0,
        language: str = "en",
        country_codes: list[str] | None = None,
        max_results: int = 10,
    ) -> ForwardGeocodeFetchResult:
        """Search for places by name using Google Maps Geocoding API."""
        self.validate_query(query)

        try:
            start_time = time.time()

            # Build request parameters for geocoding
            params = {
                "address": query.strip(),
                "key": self.api_key,
                "language": language,
            }

            # Add country/region biasing if specified
            if country_codes:
                # Google uses region parameter for country biasing
                # Use first country code as primary region
                params["region"] = country_codes[0].lower()

            # Make request to geocoding endpoint
            response = self._session.get(
                self.base_url, params=params, timeout=timeout_s
            )

            response_time = (time.time() - start_time) * 1000

            if response.status_code != 200:
                return ForwardGeocodeFetchResult(
                    ok=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    raw={"status_code": response.status_code, "text": response.text},
                )

            data = response.json()
            status = data.get("status", "UNKNOWN")

            # Handle API errors
            if status == "REQUEST_DENIED":
                error_msg = data.get("error_message", "API request denied")
                return ForwardGeocodeFetchResult(
                    ok=False, error=f"Google API error: {error_msg}", raw=data
                )
            elif status == "OVER_QUERY_LIMIT":
                return ForwardGeocodeFetchResult(
                    ok=False, error="Google API quota exceeded", raw=data
                )
            elif status == "INVALID_REQUEST":
                return ForwardGeocodeFetchResult(
                    ok=False, error="Invalid request to Google API", raw=data
                )

            # Handle empty results
            results = data.get("results", [])
            if not results or status == "ZERO_RESULTS":
                result = ForwardGeocodeResult(
                    query=query,
                    locations=[],
                    provider=ForwardGeocodeProvider(
                        name=self.name,
                        endpoint=self.base_url,
                        attribution=self.attribution,
                    ),
                    status="ZERO_RESULTS",
                    response_time_ms=response_time,
                    cache_hit=getattr(response, "from_cache", False),
                    raw_response=data,
                )
                return ForwardGeocodeFetchResult(ok=True, result=result, raw=data)

            # Parse results (limit to max_results)
            locations = []
            for item in results[:max_results]:
                try:
                    location = self._parse_google_geocoding_result(item, query)
                    if location:
                        locations.append(location)
                except Exception as e:
                    logger.warning(f"Failed to parse Google geocoding result: {e}")
                    continue

            # Create result
            result = ForwardGeocodeResult(
                query=query,
                locations=locations,
                provider=ForwardGeocodeProvider(
                    name=self.name, endpoint=self.base_url, attribution=self.attribution
                ),
                status="OK" if locations else "ZERO_RESULTS",
                response_time_ms=response_time,
                cache_hit=getattr(response, "from_cache", False),
                raw_response=data,
            )

            return ForwardGeocodeFetchResult(ok=True, result=result, raw=data)

        except Exception as e:
            logger.error(f"Google forward geocoding search failed: {e}")
            return ForwardGeocodeFetchResult(ok=False, error=str(e), raw={})

    def _parse_google_geocoding_result(
        self, data: dict[str, Any], original_query: str
    ) -> ForwardGeocodeLocation | None:
        """Parse a Google geocoding result into our standard format."""
        try:
            # Extract geometry (coordinates)
            geometry = data.get("geometry", {})
            location = geometry.get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")

            if lat is None or lng is None:
                return None

            # Basic location info
            formatted_address = data.get("formatted_address", "")

            # Parse address components
            address_components = data.get("address_components", [])

            # Extract administrative components
            country = None
            country_code = None
            state = None
            state_code = None
            county = None
            city = None
            postal_code = None

            for component in address_components:
                types = component.get("types", [])
                long_name = component.get("long_name")
                short_name = component.get("short_name")

                if "country" in types:
                    country = long_name
                    country_code = short_name
                elif "administrative_area_level_1" in types:
                    state = long_name
                    state_code = short_name
                elif "administrative_area_level_2" in types:
                    county = long_name
                elif "locality" in types:
                    city = long_name
                elif "postal_code" in types:
                    postal_code = long_name

            # Determine location type from Google place types
            place_types = data.get("types", [])
            location_type = self._determine_location_type(place_types)

            # Determine geometry type from Google location type
            location_type_info = geometry.get("location_type", "")
            geometry_type = self._map_geometry_type(location_type_info)

            # Extract bounding box (viewport)
            bounding_box = None
            viewport = geometry.get("viewport")
            if viewport:
                try:
                    northeast = viewport.get("northeast", {})
                    southwest = viewport.get("southwest", {})
                    if northeast and southwest:
                        bounding_box = BoundingBox(
                            northeast_lat=northeast.get("lat"),
                            northeast_lon=northeast.get("lng"),
                            southwest_lat=southwest.get("lat"),
                            southwest_lon=southwest.get("lng"),
                        )
                except (KeyError, TypeError):
                    bounding_box = None

            # Calculate relevance and confidence based on place types and partial match
            partial_match = data.get("partial_match", False)
            confidence = 0.9 if not partial_match else 0.6
            relevance = self._calculate_relevance(
                original_query, formatted_address, place_types
            )

            # Calculate accuracy from geometry location type
            accuracy_m = self._estimate_accuracy(location_type_info)

            # Get place ID
            place_id = data.get("place_id")

            return ForwardGeocodeLocation(
                input_query=original_query,
                formatted_address=formatted_address,
                display_name=formatted_address,  # Google doesn't separate display name
                latitude=lat,
                longitude=lng,
                country=country,
                country_code=country_code,
                state=state,
                state_code=state_code,
                county=county,
                city=city,
                postal_code=postal_code,
                location_type=location_type,
                geometry_type=geometry_type,
                bounding_box=bounding_box,
                confidence=confidence,
                relevance=relevance,
                accuracy_m=accuracy_m,
                place_id=place_id,
            )

        except Exception as e:
            logger.warning(f"Failed to parse Google geocoding result: {e}")
            return None

    def _determine_location_type(self, place_types: list[str]) -> LocationType:
        """Determine location type from Google place types."""
        # Priority order for type determination
        type_mapping = {
            "country": LocationType.COUNTRY,
            "administrative_area_level_1": LocationType.STATE,
            "locality": LocationType.CITY,
            "sublocality": LocationType.CITY,
            "postal_code": LocationType.POSTAL_CODE,
            "street_address": LocationType.ADDRESS,
            "route": LocationType.ADDRESS,
            "point_of_interest": LocationType.LANDMARK,
            "establishment": LocationType.LANDMARK,
            "natural_feature": LocationType.NATURAL_FEATURE,
            "park": LocationType.NATURAL_FEATURE,
        }

        # Return first matching type in priority order
        for place_type in place_types:
            if place_type in type_mapping:
                return type_mapping[place_type]

        return LocationType.UNKNOWN

    def _map_geometry_type(self, location_type: str) -> GeometryType | None:
        """Map Google location type to our geometry type."""
        mapping = {
            "ROOFTOP": GeometryType.ROOFTOP,
            "RANGE_INTERPOLATED": GeometryType.INTERPOLATED,
            "GEOMETRIC_CENTER": GeometryType.APPROXIMATE,
            "APPROXIMATE": GeometryType.APPROXIMATE,
        }
        return mapping.get(location_type)

    def _calculate_relevance(
        self, query: str, formatted_address: str, place_types: list[str]
    ) -> float:
        """Calculate relevance score based on query match and place types."""
        query_lower = query.lower().strip()
        address_lower = formatted_address.lower()

        # Exact match bonus
        if query_lower == address_lower:
            return 1.0

        # Check if query is contained in address
        if query_lower in address_lower:
            # Higher score if query is at the beginning
            if address_lower.startswith(query_lower):
                return 0.9
            else:
                return 0.7

        # Check individual words
        query_words = set(query_lower.split())
        address_words = set(address_lower.split())

        if query_words:
            word_match_ratio = len(query_words & address_words) / len(query_words)
            base_score = 0.3 + (word_match_ratio * 0.4)  # 0.3 to 0.7 range
        else:
            base_score = 0.2

        # Boost for more specific place types
        if any(t in place_types for t in ["street_address", "premise", "subpremise"]):
            base_score += 0.1
        elif any(t in place_types for t in ["locality", "sublocality"]):
            base_score += 0.05

        return min(1.0, base_score)

    def _estimate_accuracy(self, location_type: str) -> float | None:
        """Estimate accuracy in meters based on Google location type."""
        accuracy_mapping = {
            "ROOFTOP": 10.0,  # Building-level accuracy
            "RANGE_INTERPOLATED": 50.0,  # Street-level accuracy
            "GEOMETRIC_CENTER": 100.0,  # Block-level accuracy
            "APPROXIMATE": 1000.0,  # City-level accuracy
        }
        return accuracy_mapping.get(location_type)
