"""OpenStreetMap forward geocoding provider using Nominatim search API."""

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


class OSMForwardGeocodingProvider(ForwardGeocodingProvider):
    """OSM Nominatim forward geocoding provider (place name to coordinates)."""

    def __init__(self, base_url: str = "https://nominatim.openstreetmap.org"):
        """Initialize OSM provider."""
        self.base_url = base_url.rstrip("/")
        self._session = get_session()
        self._last_request_time = 0.0
        self._min_request_interval = 1.0  # 1 second between requests (Nominatim policy)

    @property
    def name(self) -> str:
        return "OpenStreetMap Nominatim"

    @property
    def attribution(self) -> str:
        return "© OpenStreetMap contributors"

    def is_available(self) -> bool:
        """Check if Nominatim API is available."""
        try:
            # Simple status check
            response = self._session.get(
                f"{self.base_url}/status.php",
                timeout=5,
                headers={"User-Agent": "biosample-enricher"},
            )
            return response.status_code == 200
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
        """Search for places by name using OSM Nominatim search API."""
        if not query or not query.strip():
            return ForwardGeocodeFetchResult(
                ok=False, error="Empty search query", raw={}
            )

        # Rate limiting
        self._enforce_rate_limit()

        try:
            start_time = time.time()

            # Build request parameters for search endpoint
            params = {
                "q": query.strip(),
                "format": "jsonv2",
                "addressdetails": 1,
                "extratags": 1,
                "namedetails": 1,
                "limit": min(max_results, 50),  # Nominatim limit
                "accept-language": language,
                "dedupe": 1,  # Remove duplicate results
            }

            # Add country filtering if specified
            if country_codes:
                params["countrycodes"] = ",".join(country_codes)

            # Make request to search endpoint
            response = self._session.get(
                f"{self.base_url}/search",
                params=params,
                timeout=timeout_s,
                headers={"User-Agent": "biosample-enricher"},
            )

            response_time = (time.time() - start_time) * 1000

            if response.status_code != 200:
                return ForwardGeocodeFetchResult(
                    ok=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    raw={"status_code": response.status_code, "text": response.text},
                )

            data = response.json()

            # Handle empty results
            if not data:
                result = ForwardGeocodeResult(
                    query=query,
                    locations=[],
                    provider=ForwardGeocodeProvider(
                        name=self.name,
                        endpoint=f"{self.base_url}/search",
                        attribution=self.attribution,
                    ),
                    status="ZERO_RESULTS",
                    response_time_ms=response_time,
                    cache_hit=getattr(response, "from_cache", False),
                    raw_response=data,
                )
                return ForwardGeocodeFetchResult(ok=True, result=result, raw=data)

            # Parse results
            locations = []
            for item in data:
                try:
                    location = self._parse_nominatim_search_result(item, query)
                    if location:
                        locations.append(location)
                except Exception as e:
                    logger.warning(f"Failed to parse OSM search result: {e}")
                    continue

            # Create result
            result = ForwardGeocodeResult(
                query=query,
                locations=locations,
                provider=ForwardGeocodeProvider(
                    name=self.name,
                    endpoint=f"{self.base_url}/search",
                    attribution=self.attribution,
                ),
                status="OK" if locations else "ZERO_RESULTS",
                response_time_ms=response_time,
                cache_hit=getattr(response, "from_cache", False),
                raw_response=data,
            )

            return ForwardGeocodeFetchResult(ok=True, result=result, raw=data)

        except Exception as e:
            logger.error(f"OSM forward geocoding search failed: {e}")
            return ForwardGeocodeFetchResult(ok=False, error=str(e), raw={})

    def _enforce_rate_limit(self) -> None:
        """Enforce Nominatim rate limiting policy."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _parse_nominatim_search_result(
        self, data: dict[str, Any], original_query: str
    ) -> ForwardGeocodeLocation | None:
        """Parse a Nominatim search result into our standard format."""
        try:
            # Basic coordinates (the main output)
            lat = float(data.get("lat", 0))
            lon = float(data.get("lon", 0))

            # Extract address components
            address = data.get("address", {})

            # Basic location info
            formatted_address = data.get("display_name", "")

            # Administrative components
            country = self._get_address_component(address, ["country"])
            country_code = self._get_address_component(address, ["country_code"])
            state = self._get_address_component(
                address, ["state", "province", "region"]
            )
            county = self._get_address_component(address, ["county", "district"])
            city = self._get_address_component(
                address, ["city", "town", "village", "municipality"]
            )
            postal_code = self._get_address_component(
                address, ["postcode", "postal_code"]
            )

            # Determine location type from OSM data
            location_type = self._determine_location_type(data)

            # Calculate relevance based on display name similarity to query
            relevance = self._calculate_relevance(
                original_query, formatted_address, data
            )

            # Get importance and confidence
            importance = data.get("importance", 0.0)
            confidence = (
                min(1.0, importance * 2.0) if importance else 0.5
            )  # Scale importance to confidence

            # Extract bounding box if available
            bounding_box = None
            if all(key in data for key in ["boundingbox"]):
                try:
                    bbox = data["boundingbox"]
                    if len(bbox) >= 4:
                        bounding_box = BoundingBox(
                            southwest_lat=float(bbox[0]),
                            northeast_lat=float(bbox[1]),
                            southwest_lon=float(bbox[2]),
                            northeast_lon=float(bbox[3]),
                        )
                except (ValueError, IndexError, TypeError):
                    bounding_box = None

            # External identifiers
            osm_id = data.get("osm_id")
            osm_type = data.get("osm_type")
            place_id = data.get("place_id")

            return ForwardGeocodeLocation(
                input_query=original_query,
                formatted_address=formatted_address,
                display_name=data.get("name") or data.get("display_name"),
                latitude=lat,
                longitude=lon,
                country=country,
                country_code=country_code.upper() if country_code else None,
                state=state,
                county=county,
                city=city,
                postal_code=postal_code,
                location_type=location_type,
                geometry_type=GeometryType.POINT,  # OSM typically returns points
                bounding_box=bounding_box,
                confidence=confidence,
                relevance=relevance,
                place_id=str(place_id) if place_id else None,
                osm_id=str(osm_id) if osm_id else None,
                osm_type=osm_type,
                importance=importance,
            )

        except Exception as e:
            logger.warning(f"Failed to parse OSM search result: {e}")
            return None

    def _get_address_component(
        self, address: dict[str, Any], fields: list[str]
    ) -> str | None:
        """Get first available address component from field list."""
        for field in fields:
            if field in address and address[field]:
                return str(address[field])
        return None

    def _determine_location_type(self, data: dict[str, Any]) -> LocationType:
        """Determine location type from OSM data."""
        osm_class = data.get("class", "")
        osm_type = data.get("type", "")

        # Type mapping based on OSM class and type
        if osm_class == "place":
            if osm_type in ["country"]:
                return LocationType.COUNTRY
            elif osm_type in ["state", "province"]:
                return LocationType.STATE
            elif osm_type in ["city", "town"]:
                return LocationType.CITY
            elif osm_type in ["village", "hamlet"]:
                return LocationType.VILLAGE
        elif osm_class == "boundary" and osm_type == "administrative":
            return LocationType.ADMINISTRATIVE_AREA
        elif osm_class == "highway":
            return LocationType.ADDRESS
        elif osm_class == "natural":
            return LocationType.NATURAL_FEATURE
        elif osm_class == "amenity":
            return LocationType.LANDMARK

        return LocationType.UNKNOWN

    def _calculate_relevance(
        self, query: str, display_name: str, data: dict[str, Any]
    ) -> float:
        """Calculate relevance score based on query match."""
        query_lower = query.lower().strip()
        display_lower = display_name.lower()

        # Exact match bonus
        if query_lower == display_lower:
            return 1.0

        # Check if query is contained in display name
        if query_lower in display_lower:
            # Higher score if query is at the beginning
            if display_lower.startswith(query_lower):
                return 0.9
            else:
                return 0.7

        # Check individual words
        query_words = set(query_lower.split())
        display_words = set(display_lower.split())

        if query_words:
            word_match_ratio = len(query_words & display_words) / len(query_words)
            return 0.3 + (word_match_ratio * 0.4)  # 0.3 to 0.7 range

        # Use OSM importance as fallback
        importance = data.get("importance", 0.0)
        return min(0.5, importance) if importance else 0.2
