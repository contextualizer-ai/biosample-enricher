"""Google Geocoding API reverse geocoding provider."""

import os
import time
from typing import Any

from ...http_cache import request
from ...logging_config import get_logger
from ...reverse_geocoding_models import (
    AddressComponent,
    AddressComponentType,
    BoundingBox,
    PlaceType,
    ReverseGeocodeFetchResult,
    ReverseGeocodeLocation,
    ReverseGeocodeProvider,
    ReverseGeocodeResult,
)
from .base import BaseReverseGeocodingProvider

logger = get_logger(__name__)


class GoogleReverseGeocodingProvider(BaseReverseGeocodingProvider):
    """Provider for Google Geocoding API reverse geocoding."""

    # Mapping of Google address component types to our types
    COMPONENT_TYPE_MAPPING = {
        "country": AddressComponentType.COUNTRY,
        "administrative_area_level_1": AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_1,
        "administrative_area_level_2": AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_2,
        "administrative_area_level_3": AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_3,
        "administrative_area_level_4": AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_4,
        "administrative_area_level_5": AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_5,
        "locality": AddressComponentType.LOCALITY,
        "sublocality": AddressComponentType.SUBLOCALITY,
        "sublocality_level_1": AddressComponentType.SUBLOCALITY_LEVEL_1,
        "sublocality_level_2": AddressComponentType.SUBLOCALITY_LEVEL_2,
        "sublocality_level_3": AddressComponentType.SUBLOCALITY_LEVEL_3,
        "sublocality_level_4": AddressComponentType.SUBLOCALITY_LEVEL_4,
        "sublocality_level_5": AddressComponentType.SUBLOCALITY_LEVEL_5,
        "route": AddressComponentType.ROUTE,
        "street_number": AddressComponentType.STREET_NUMBER,
        "street_address": AddressComponentType.STREET_ADDRESS,
        "premise": AddressComponentType.PREMISE,
        "subpremise": AddressComponentType.SUBPREMISE,
        "postal_code": AddressComponentType.POSTAL_CODE,
        "postal_code_prefix": AddressComponentType.POSTAL_CODE_PREFIX,
        "postal_code_suffix": AddressComponentType.POSTAL_CODE_SUFFIX,
        "natural_feature": AddressComponentType.NATURAL_FEATURE,
        "park": AddressComponentType.PARK,
        "point_of_interest": AddressComponentType.POINT_OF_INTEREST,
        "establishment": AddressComponentType.ESTABLISHMENT,
        "neighborhood": AddressComponentType.NEIGHBORHOOD,
        "colloquial_area": AddressComponentType.COLLOQUIAL_AREA,
        "plus_code": AddressComponentType.PLUS_CODE,
        "political": AddressComponentType.POLITICAL,
        "intersection": AddressComponentType.INTERSECTION,
        "continent": AddressComponentType.CONTINENT,
    }

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize Google Geocoding reverse geocoding provider.

        Args:
            api_key: Google API key (if None, reads from GOOGLE_MAIN_API_KEY env var)
        """
        super().__init__(
            name="google_geocoding",
            endpoint="https://maps.googleapis.com/maps/api/geocode/json",
            api_version="v1",
        )

        self.api_key = api_key or os.getenv("GOOGLE_MAIN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_MAIN_API_KEY environment variable "
                "or pass api_key parameter."
            )

        logger.info("Google Geocoding provider initialized")

    def fetch(
        self,
        lat: float,
        lon: float,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
        language: str = "en",
        limit: int = 10,
    ) -> ReverseGeocodeFetchResult:
        """
        Fetch reverse geocoding data from Google Geocoding API.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results
            limit: Maximum number of results (Google may return more)

        Returns:
            Fetch result with reverse geocoding data
        """
        self._validate_coordinates(lat, lon)

        logger.debug(
            f"Fetching reverse geocoding from Google API: {lat:.6f}, {lon:.6f}"
        )

        start_time = time.time()
        try:
            # Prepare request parameters
            params = {
                "latlng": f"{lat},{lon}",
                "key": self.api_key,
                "language": language,
                # Google doesn't have a direct limit param, but we can use result_type
                # to filter results
            }

            # Make request using cached HTTP client
            response = request(
                "GET",
                self.endpoint,
                read_from_cache=read_from_cache,
                write_to_cache=write_to_cache,
                params=params,
                timeout=timeout_s,
            )

            response_time_ms = (time.time() - start_time) * 1000
            response.raise_for_status()
            data = response.json()

            # Check for cache hit (from_cache attribute may not exist)
            cache_hit = getattr(response, "from_cache", False)
            return self._parse_response(
                lat, lon, data, response_time_ms, cache_hit=cache_hit, limit=limit
            )

        except Exception as e:
            logger.error(f"Google Geocoding API error: {e}")
            return ReverseGeocodeFetchResult(ok=False, error=str(e), raw={})

    def _parse_response(
        self,
        lat: float,
        lon: float,
        data: dict[str, Any],
        response_time_ms: float,
        cache_hit: bool,
        limit: int,
    ) -> ReverseGeocodeFetchResult:
        """
        Parse Google Geocoding API response.

        Args:
            lat: Requested latitude
            lon: Requested longitude
            data: API response data
            response_time_ms: Response time in milliseconds
            cache_hit: Whether response was from cache
            limit: Maximum number of results to return

        Returns:
            Parsed fetch result
        """
        try:
            # Check API status
            status = data.get("status")
            error_message = data.get("error_message")

            if status not in ["OK", "ZERO_RESULTS"]:
                error_msg = error_message or f"API returned status: {status}"
                logger.warning(f"Google API error: {error_msg}")
                return ReverseGeocodeFetchResult(ok=False, error=error_msg, raw=data)

            # Extract results
            results = data.get("results", [])

            # Parse locations (limit to requested number)
            locations = []
            for i, result in enumerate(results[:limit]):
                location = self._parse_location(result, lat, lon)
                if location:
                    # Add confidence based on order (first result is most confident)
                    location.confidence = max(0.5, 1.0 - (i * 0.1))
                    locations.append(location)

            provider = ReverseGeocodeProvider(
                name=self.name,
                endpoint=self.endpoint,
                api_version=self.api_version,
                rate_limit=50,  # Google allows up to 50 QPS
            )

            result = ReverseGeocodeResult(
                query_lat=lat,
                query_lon=lon,
                locations=locations,
                provider=provider,
                status=status,
                error_message=error_message,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                raw_response=data,
            )

            return ReverseGeocodeFetchResult(ok=True, result=result, raw=data)

        except Exception as e:
            logger.error(f"Error parsing Google response: {e}")
            return ReverseGeocodeFetchResult(
                ok=False, error=f"Response parsing error: {e}", raw=data
            )

    def _parse_location(
        self, result: dict[str, Any], query_lat: float, query_lon: float
    ) -> ReverseGeocodeLocation | None:
        """
        Parse a single location from Google response.

        Args:
            result: Single result from Google API
            query_lat: Query latitude
            query_lon: Query longitude

        Returns:
            Parsed location or None if invalid
        """
        try:
            # Extract basic information
            formatted_address = result.get("formatted_address", "")
            place_id = result.get("place_id", "")

            # Parse geometry
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})
            lat = location.get("lat", query_lat)
            lon = location.get("lng", query_lon)

            # Parse bounding box from viewport
            bounding_box = None
            viewport = geometry.get("viewport")
            if viewport:
                northeast = viewport.get("northeast", {})
                southwest = viewport.get("southwest", {})
                if northeast and southwest:
                    bounding_box = BoundingBox(
                        north=northeast.get("lat", lat),
                        south=southwest.get("lat", lat),
                        east=northeast.get("lng", lon),
                        west=southwest.get("lng", lon),
                    )

            # Parse address components
            address_components = result.get("address_components", [])
            components = self._parse_address_components(address_components)

            # Extract common fields from components
            country = None
            country_code = None
            state = None
            state_code = None
            county = None
            city = None
            suburb = None
            postcode = None
            road = None
            house_number = None

            for comp in address_components:
                types = comp.get("types", [])
                long_name = comp.get("long_name", "")
                short_name = comp.get("short_name", "")

                if "country" in types:
                    country = long_name
                    country_code = short_name.upper()
                elif "administrative_area_level_1" in types:
                    state = long_name
                    state_code = short_name
                elif "administrative_area_level_2" in types:
                    county = long_name
                elif "locality" in types:
                    city = long_name
                elif "sublocality" in types or "sublocality_level_1" in types:
                    suburb = long_name
                elif "postal_code" in types:
                    postcode = long_name
                elif "route" in types:
                    road = long_name
                elif "street_number" in types:
                    house_number = long_name

            # Determine place type from Google types
            place_type = self._determine_place_type(result.get("types", []))

            # Calculate distance from query point
            distance_m = self._calculate_distance(query_lat, query_lon, lat, lon)

            return ReverseGeocodeLocation(
                formatted_address=formatted_address,
                display_name=formatted_address,
                components=components,
                country=country,
                country_code=country_code,
                state=state,
                state_code=state_code,
                county=county,
                city=city,
                suburb=suburb,
                postcode=postcode,
                road=road,
                house_number=house_number,
                house_name=None,  # Google doesn't provide house names
                place_type=place_type,
                place_rank=None,  # Google doesn't provide place rank
                importance=None,  # Google doesn't provide importance score
                lat=lat,
                lon=lon,
                bounding_box=bounding_box,
                place_id=place_id,
                osm_id=None,  # Google doesn't provide OSM IDs
                osm_type=None,
                wikidata_id=None,  # Google doesn't provide Wikidata IDs
                wikipedia_url=None,
                licence="Google Maps Platform Terms of Service",
                attribution="Google",
                distance_m=distance_m,
            )

        except Exception as e:
            import traceback

            logger.warning(f"Error parsing location result: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

    def _parse_address_components(
        self, components: list[dict[str, Any]]
    ) -> list[AddressComponent]:
        """
        Parse Google address components into structured components.

        Args:
            components: List of address components from Google

        Returns:
            List of parsed address components
        """
        parsed_components = []

        for comp in components:
            types = comp.get("types", [])
            long_name = comp.get("long_name", "")
            short_name = comp.get("short_name", "")

            # Find the first matching type
            for google_type in types:
                if google_type in self.COMPONENT_TYPE_MAPPING:
                    component_type = self.COMPONENT_TYPE_MAPPING[google_type]
                    parsed_components.append(
                        AddressComponent(
                            type=component_type,
                            short_name=short_name,
                            long_name=long_name,
                            confidence=1.0,  # Google doesn't provide confidence scores
                        )
                    )
                    break  # Only use the first matching type

        return parsed_components

    def _determine_place_type(self, types: list[str]) -> PlaceType | None:
        """
        Determine place type from Google types.

        Args:
            types: List of Google place types

        Returns:
            Place type or None
        """
        # Map Google types to our PlaceType enum
        type_mapping = {
            "establishment": PlaceType.ESTABLISHMENT,
            "point_of_interest": PlaceType.POINT_OF_INTEREST,
            "natural_feature": PlaceType.NATURAL,
            "park": PlaceType.PARK,
            "route": PlaceType.HIGHWAY,
            "street_address": PlaceType.BUILDING,
            "premise": PlaceType.BUILDING,
            "airport": PlaceType.AEROWAY,
            "train_station": PlaceType.RAILWAY,
            "bus_station": PlaceType.AMENITY,
            "tourist_attraction": PlaceType.TOURISM,
            "place_of_worship": PlaceType.AMENITY,
            "store": PlaceType.SHOP,
            "restaurant": PlaceType.AMENITY,
            "hospital": PlaceType.AMENITY,
            "school": PlaceType.AMENITY,
            "university": PlaceType.AMENITY,
        }

        for google_type in types:
            if google_type in type_mapping:
                return type_mapping[google_type]

        # Default to PLACE if we have location-based types
        if any(
            t in ["political", "locality", "administrative_area_level_1"] for t in types
        ):
            return PlaceType.PLACE

        return PlaceType.OTHER

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points in meters using Haversine formula.

        Args:
            lat1: First point latitude
            lon1: First point longitude
            lat2: Second point latitude
            lon2: Second point longitude

        Returns:
            Distance in meters
        """
        from math import cos, radians, sin

        R = 6371000  # Earth's radius in meters

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        )
        c = 2 * (a**0.5)

        return float(R * c)
