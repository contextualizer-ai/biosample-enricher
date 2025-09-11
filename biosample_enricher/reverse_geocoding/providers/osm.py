"""OpenStreetMap Nominatim reverse geocoding provider."""

import time
from typing import Any

from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.reverse_geocoding.providers.base import (
    BaseReverseGeocodingProvider,
)
from biosample_enricher.reverse_geocoding_models import (
    AddressComponent,
    AddressComponentType,
    BoundingBox,
    PlaceType,
    ReverseGeocodeFetchResult,
    ReverseGeocodeLocation,
    ReverseGeocodeProvider,
    ReverseGeocodeResult,
)

logger = get_logger(__name__)


class OSMReverseGeocodingProvider(BaseReverseGeocodingProvider):
    """Provider for OpenStreetMap Nominatim reverse geocoding API."""

    def __init__(
        self,
        endpoint: str = "https://nominatim.openstreetmap.org/reverse",
        user_agent: str = "biosample-enricher/1.0",
    ) -> None:
        """
        Initialize OSM Nominatim reverse geocoding provider.

        Args:
            endpoint: API endpoint URL (defaults to public Nominatim)
            user_agent: User agent string for API requests
        """
        super().__init__(name="osm_nominatim", endpoint=endpoint, api_version="v1")
        self.user_agent = user_agent
        self.last_request_time = 0.0
        self.min_request_interval = 1.0  # Respect Nominatim rate limit (1 req/sec)
        logger.info(f"OSM Nominatim provider initialized: {endpoint}")

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
        Fetch reverse geocoding data from OSM Nominatim API.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds
            language: Language code for results
            limit: Maximum number of results to return

        Returns:
            Fetch result with reverse geocoding data
        """
        self._validate_coordinates(lat, lon)

        # Enforce rate limiting for public Nominatim
        if "nominatim.openstreetmap.org" in self.endpoint:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            self.last_request_time = time.time()

        logger.debug(f"Fetching reverse geocoding from Nominatim: {lat:.6f}, {lon:.6f}")

        start_time = time.time()
        try:
            # Prepare request parameters
            params = {
                "lat": str(lat),
                "lon": str(lon),
                "format": "jsonv2",
                "addressdetails": "1",
                "extratags": "1",
                "namedetails": "1",
                "limit": str(limit),
                "accept-language": language,
            }

            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }

            # Make request using cached HTTP client
            response = request(
                "GET",
                self.endpoint,
                read_from_cache=read_from_cache,
                write_to_cache=write_to_cache,
                params=params,
                headers=headers,
                timeout=timeout_s,
            )

            response_time_ms = (time.time() - start_time) * 1000
            response.raise_for_status()
            data = response.json()

            # Check for cache hit (from_cache attribute may not exist)
            cache_hit = getattr(response, "from_cache", False)
            return self._parse_response(
                lat, lon, data, response_time_ms, cache_hit=cache_hit
            )

        except Exception as e:
            logger.error(f"OSM Nominatim API error: {e}")
            return ReverseGeocodeFetchResult(ok=False, error=str(e), raw={})

    def _parse_response(
        self,
        lat: float,
        lon: float,
        data: dict[str, Any] | list[dict[str, Any]],
        response_time_ms: float,
        cache_hit: bool,
    ) -> ReverseGeocodeFetchResult:
        """
        Parse OSM Nominatim API response.

        Args:
            lat: Requested latitude
            lon: Requested longitude
            data: API response data
            response_time_ms: Response time in milliseconds
            cache_hit: Whether response was from cache

        Returns:
            Parsed fetch result
        """
        try:
            # Nominatim returns a single object or array depending on limit
            # Convert single result to list for uniform processing
            data_list = [data] if isinstance(data, dict) else data

            locations = []
            for item in data_list:
                location = self._parse_location(item)
                if location:
                    locations.append(location)

            if not locations:
                return ReverseGeocodeFetchResult(
                    ok=False, error="No locations found", raw={"response": data}
                )

            provider = ReverseGeocodeProvider(
                name=self.name,
                endpoint=self.endpoint,
                api_version=self.api_version,
                rate_limit=1,  # 1 request per second for public Nominatim
            )

            result = ReverseGeocodeResult(
                query_lat=lat,
                query_lon=lon,
                locations=locations,
                provider=provider,
                status="OK",
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                raw_response={"results": data},
            )

            return ReverseGeocodeFetchResult(
                ok=True, result=result, raw={"response": data}
            )

        except Exception as e:
            logger.error(f"Error parsing Nominatim response: {e}")
            return ReverseGeocodeFetchResult(
                ok=False, error=f"Response parsing error: {e}", raw={"response": data}
            )

    def _parse_location(self, item: dict[str, Any]) -> ReverseGeocodeLocation | None:
        """
        Parse a single location from Nominatim response.

        Args:
            item: Single location item from response

        Returns:
            Parsed location or None if invalid
        """
        try:
            # Check if item is valid
            if not item or not isinstance(item, dict):
                return None
                
            # Extract basic information
            display_name = item.get("display_name", "")
            place_id = str(item.get("place_id", ""))
            osm_type = item.get("osm_type")
            osm_id = str(item.get("osm_id", ""))

            # Parse coordinates
            lat = float(item.get("lat", 0))
            lon = float(item.get("lon", 0))

            # Parse bounding box if available
            bounding_box = None
            if "boundingbox" in item and len(item["boundingbox"]) == 4:
                bbox = item["boundingbox"]
                bounding_box = BoundingBox(
                    south=float(bbox[0]),
                    north=float(bbox[1]),
                    west=float(bbox[2]),
                    east=float(bbox[3]),
                )

            # Parse address components
            address = item.get("address", {})
            components = self._parse_address_components(address)

            # Extract common fields
            country = address.get("country")
            country_code = address.get("country_code", "").upper()
            state = (
                address.get("state") or address.get("province") or address.get("region")
            )
            county = address.get("county") or address.get("district")
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
            )
            suburb = (
                address.get("suburb")
                or address.get("neighbourhood")
                or address.get("quarter")
            )
            postcode = address.get("postcode") or address.get("postal_code")
            road = address.get("road") or address.get("street")
            house_number = address.get("house_number")
            house_name = address.get("house_name") or address.get("building")

            # Determine place type
            place_type = self._determine_place_type(item)

            # Parse extra tags
            extratags = item.get("extratags", {})
            wikidata_id = extratags.get("wikidata")
            wikipedia = extratags.get("wikipedia")
            wikipedia_url = (
                f"https://wikipedia.org/wiki/{wikipedia}" if wikipedia else None
            )

            # Calculate importance and confidence
            importance = item.get("importance")
            if importance is not None:
                importance = float(importance)
                confidence = min(1.0, importance)  # Normalize to 0-1
            else:
                confidence = None

            # Get place rank
            place_rank = item.get("place_rank")
            if place_rank is not None:
                place_rank = int(place_rank)

            return ReverseGeocodeLocation(
                formatted_address=display_name,
                display_name=display_name,
                components=components,
                country=country,
                country_code=country_code,
                state=state,
                state_code=None,  # OSM doesn't provide state codes
                county=county,
                city=city,
                suburb=suburb,
                postcode=postcode,
                road=road,
                house_number=house_number,
                house_name=house_name,
                place_type=place_type,
                place_rank=place_rank,
                importance=importance,
                lat=lat,
                lon=lon,
                bounding_box=bounding_box,
                place_id=place_id,
                osm_id=osm_id,
                osm_type=osm_type,
                wikidata_id=wikidata_id,
                wikipedia_url=wikipedia_url,
                licence="Data © OpenStreetMap contributors, ODbL 1.0",
                attribution="OpenStreetMap",
                confidence=confidence,
            )

        except Exception as e:
            logger.warning(f"Error parsing location item: {e}")
            return None

    def _parse_address_components(
        self, address: dict[str, Any]
    ) -> list[AddressComponent]:
        """
        Parse address dictionary into structured components.

        Args:
            address: Address dictionary from Nominatim

        Returns:
            List of address components
        """
        components = []

        # Mapping of OSM address keys to component types
        mappings = [
            ("country", AddressComponentType.COUNTRY),
            ("state", AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_1),
            ("province", AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_1),
            ("region", AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_1),
            ("county", AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_2),
            ("district", AddressComponentType.ADMINISTRATIVE_AREA_LEVEL_3),
            ("city", AddressComponentType.LOCALITY),
            ("town", AddressComponentType.LOCALITY),
            ("village", AddressComponentType.LOCALITY),
            ("municipality", AddressComponentType.LOCALITY),
            ("suburb", AddressComponentType.SUBLOCALITY),
            ("neighbourhood", AddressComponentType.NEIGHBORHOOD),
            ("quarter", AddressComponentType.NEIGHBORHOOD),
            ("road", AddressComponentType.ROUTE),
            ("street", AddressComponentType.ROUTE),
            ("house_number", AddressComponentType.STREET_NUMBER),
            ("postcode", AddressComponentType.POSTAL_CODE),
            ("postal_code", AddressComponentType.POSTAL_CODE),
        ]

        for key, component_type in mappings:
            value = address.get(key)
            if value:
                components.append(
                    AddressComponent(
                        type=component_type,
                        short_name=str(value),
                        long_name=str(value),
                    )
                )

        return components

    def _determine_place_type(self, item: dict[str, Any]) -> PlaceType | None:
        """
        Determine place type from OSM data.

        Args:
            item: Location item from Nominatim

        Returns:
            Place type or None
        """
        # Check the 'type' field
        osm_type = item.get("type", "").lower()

        # Map common OSM types to our PlaceType enum
        type_mapping = {
            "building": PlaceType.BUILDING,
            "house": PlaceType.HOUSE,
            "amenity": PlaceType.AMENITY,
            "shop": PlaceType.SHOP,
            "tourism": PlaceType.TOURISM,
            "historic": PlaceType.HISTORIC,
            "leisure": PlaceType.LEISURE,
            "natural": PlaceType.NATURAL,
            "landuse": PlaceType.LANDUSE,
            "waterway": PlaceType.WATERWAY,
            "highway": PlaceType.HIGHWAY,
            "railway": PlaceType.RAILWAY,
            "aeroway": PlaceType.AEROWAY,
            "boundary": PlaceType.BOUNDARY,
            "place": PlaceType.PLACE,
            "office": PlaceType.OFFICE,
            "emergency": PlaceType.EMERGENCY,
            "military": PlaceType.MILITARY,
            "craft": PlaceType.CRAFT,
            "man_made": PlaceType.MAN_MADE,
        }

        for key, place_type in type_mapping.items():
            if key in osm_type:
                return place_type

        # Check category field
        category = item.get("category", "").lower()
        for key, place_type in type_mapping.items():
            if key in category:
                return place_type

        return PlaceType.OTHER
