"""Google Places API provider for geographic features enrichment."""

import os
import time
from typing import Any

from biosample_enricher.http_cache import request
from biosample_enricher.logging_config import get_logger
from biosample_enricher.osm_features.models import (
    Coordinates,
    FeatureCategory,
    GooglePlacesFeature,
    GooglePlacesFetchResult,
    GooglePlacesResult,
)

logger = get_logger(__name__)


class GooglePlacesProvider:
    """Provider for Google Places API geographic features."""

    # Google Places types to our feature categories
    PLACES_TYPE_MAPPING = {
        # Natural features
        "park": FeatureCategory.NATURAL,
        "campground": FeatureCategory.NATURAL,
        "national_park": FeatureCategory.NATURAL,
        "zoo": FeatureCategory.NATURAL,
        "aquarium": FeatureCategory.NATURAL,
        # Transport
        "airport": FeatureCategory.HIGHWAY,
        "bus_station": FeatureCategory.HIGHWAY,
        "subway_station": FeatureCategory.HIGHWAY,
        "train_station": FeatureCategory.HIGHWAY,
        "transit_station": FeatureCategory.HIGHWAY,
        "taxi_stand": FeatureCategory.HIGHWAY,
        "gas_station": FeatureCategory.HIGHWAY,
        # Buildings
        "establishment": FeatureCategory.BUILDING,
        "premise": FeatureCategory.BUILDING,
        "subpremise": FeatureCategory.BUILDING,
        # Amenities
        "restaurant": FeatureCategory.AMENITY,
        "food": FeatureCategory.AMENITY,
        "meal_takeaway": FeatureCategory.AMENITY,
        "cafe": FeatureCategory.AMENITY,
        "bar": FeatureCategory.AMENITY,
        "hospital": FeatureCategory.AMENITY,
        "pharmacy": FeatureCategory.AMENITY,
        "doctor": FeatureCategory.AMENITY,
        "dentist": FeatureCategory.AMENITY,
        "veterinary_care": FeatureCategory.AMENITY,
        "school": FeatureCategory.AMENITY,
        "university": FeatureCategory.AMENITY,
        "library": FeatureCategory.AMENITY,
        "museum": FeatureCategory.AMENITY,
        "amusement_park": FeatureCategory.AMENITY,
        "bowling_alley": FeatureCategory.AMENITY,
        "casino": FeatureCategory.AMENITY,
        "movie_theater": FeatureCategory.AMENITY,
        "night_club": FeatureCategory.AMENITY,
        "shopping_mall": FeatureCategory.AMENITY,
        "store": FeatureCategory.AMENITY,
        "supermarket": FeatureCategory.AMENITY,
        "bank": FeatureCategory.AMENITY,
        "atm": FeatureCategory.AMENITY,
        "post_office": FeatureCategory.AMENITY,
        "police": FeatureCategory.AMENITY,
        "fire_station": FeatureCategory.AMENITY,
        "courthouse": FeatureCategory.AMENITY,
        "embassy": FeatureCategory.AMENITY,
        "city_hall": FeatureCategory.AMENITY,
        "gym": FeatureCategory.AMENITY,
        "beauty_salon": FeatureCategory.AMENITY,
        "hair_care": FeatureCategory.AMENITY,
        "spa": FeatureCategory.AMENITY,
        "laundry": FeatureCategory.AMENITY,
        "car_wash": FeatureCategory.AMENITY,
        "car_repair": FeatureCategory.AMENITY,
        "church": FeatureCategory.AMENITY,
        "mosque": FeatureCategory.AMENITY,
        "synagogue": FeatureCategory.AMENITY,
        "hindu_temple": FeatureCategory.AMENITY,
        "place_of_worship": FeatureCategory.AMENITY,
        "cemetery": FeatureCategory.AMENITY,
        "funeral_home": FeatureCategory.AMENITY,
        "lodging": FeatureCategory.AMENITY,
        "tourist_attraction": FeatureCategory.AMENITY,
        "travel_agency": FeatureCategory.AMENITY,
        # Land use
        "real_estate_agency": FeatureCategory.LANDUSE,
        "storage": FeatureCategory.LANDUSE,
    }

    def __init__(self, api_key: str | None = None):
        """
        Initialize Google Places provider.

        Args:
            api_key: Google API key (if None, reads from GOOGLE_MAIN_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_MAIN_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"

        # Rate limiting: Google Places allows 1000 requests per 24 hours for free tier
        self.min_request_interval = 1.0  # 1 second between requests
        self.last_request_time = 0.0

        logger.info("Google Places provider initialized")

    def is_available(self) -> bool:
        """Check if Google Places API is available."""
        if not self.api_key:
            logger.warning("Google API key not provided")
            return False

        try:
            # Test with a simple request to a known location
            test_response = request(
                "GET",
                self.base_url,
                params={
                    "location": "37.7749,-122.4194",  # San Francisco
                    "radius": "100",
                    "key": self.api_key,
                },
                timeout=10,
                read_from_cache=True,
                write_to_cache=False,  # Don't cache test requests
            )

            data = test_response.json()
            status = data.get("status", "")

            if status in ["OK", "ZERO_RESULTS"]:
                return True
            elif status == "REQUEST_DENIED":
                logger.error(
                    "Google Places API key is invalid or insufficient permissions"
                )
                return False
            else:
                logger.warning(f"Google Places API test returned status: {status}")
                return False

        except Exception as e:
            logger.warning(f"Error testing Google Places API availability: {e}")
            return False

    def get_features(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 1000,
        timeout_s: int = 180,
    ) -> GooglePlacesFetchResult:
        """
        Get geographic features from Google Places API.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_m: Search radius in meters (max 50,000 for Google Places)
            timeout_s: Request timeout in seconds

        Returns:
            Fetch result with Google Places features
        """
        if not self.is_available():
            return GooglePlacesFetchResult(
                ok=False,
                error="Google Places API not available",
                raw={},
            )

        # Enforce rate limiting
        self._enforce_rate_limit()

        # Google Places API has a maximum radius of 50,000 meters
        radius_m = min(radius_m, 50000)

        logger.info(
            f"Fetching Google Places features for {latitude}, {longitude} within {radius_m}m"
        )

        try:
            # Initial request - get up to 60 results (3 pages of 20 each)
            all_places = []
            next_page_token = None
            page_count = 0
            max_pages = 3  # Limit to avoid excessive API usage

            while page_count < max_pages:
                params = {
                    "location": f"{latitude},{longitude}",
                    "radius": str(radius_m),
                    "key": self.api_key,
                }

                if next_page_token:
                    params["pagetoken"] = next_page_token
                    # Google requires a delay before using page tokens
                    time.sleep(2)

                response = request(
                    "GET",
                    self.base_url,
                    params=params,
                    timeout=timeout_s,
                    read_from_cache=True,
                    write_to_cache=True,
                )

                response.raise_for_status()
                data = response.json()

                status = data.get("status", "")
                if status not in ["OK", "ZERO_RESULTS"]:
                    error_message = data.get(
                        "error_message", f"API returned status: {status}"
                    )
                    logger.error(f"Google Places API error: {error_message}")
                    return GooglePlacesFetchResult(
                        ok=False,
                        error=error_message,
                        raw=data,
                    )

                # Add results from this page
                places = data.get("results", [])
                all_places.extend(places)

                # Check for next page
                next_page_token = data.get("next_page_token")
                page_count += 1

                if not next_page_token or status == "ZERO_RESULTS":
                    break

                logger.debug(f"Retrieved page {page_count} with {len(places)} places")

            logger.info(
                f"Retrieved {len(all_places)} total places from Google Places API"
            )

            # Parse the results
            return self._parse_response(latitude, longitude, all_places, radius_m)

        except Exception as e:
            logger.error(f"Error fetching Google Places features: {e}")
            return GooglePlacesFetchResult(
                ok=False,
                error=str(e),
                raw={},
            )

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _parse_response(
        self,
        query_lat: float,
        query_lon: float,
        places: list[dict[str, Any]],
        radius_m: int,
    ) -> GooglePlacesFetchResult:
        """
        Parse Google Places API response into our feature format.

        Args:
            query_lat: Query latitude
            query_lon: Query longitude
            places: List of place results from API
            radius_m: Search radius used

        Returns:
            Parsed fetch result
        """
        try:
            parsed_features = []
            category_counts = {}

            for place in places:
                # Parse individual place
                feature = self._parse_place(place, query_lat, query_lon)
                if feature:
                    parsed_features.append(feature)

                    # Count by category for unnamed aggregation
                    category = feature.category.value
                    if category not in category_counts:
                        category_counts[category] = 0
                    category_counts[category] += 1

            # Sort by distance
            parsed_features.sort(key=lambda f: f.distance_km or float("inf"))

            # Separate named vs unnamed features
            named_features = [f for f in parsed_features if f.name]
            unnamed_counts = []

            # For Google Places, most results have names, but we can still aggregate by type
            for category, count in category_counts.items():
                unnamed_counts.append(
                    {
                        "key": category,
                        "total_count": count,
                    }
                )

            result = GooglePlacesResult(
                query=Coordinates(latitude=query_lat, longitude=query_lon),
                radius_m=radius_m,
                named_features=named_features,
                unnamed_counts=unnamed_counts,
                total_features=len(parsed_features),
                success=True,
                provider="google_places",
            )

            return GooglePlacesFetchResult(
                ok=True,
                result=result,
                raw={"places": places},
            )

        except Exception as e:
            logger.error(f"Error parsing Google Places response: {e}")
            return GooglePlacesFetchResult(
                ok=False,
                error=f"Response parsing error: {e}",
                raw={"places": places},
            )

    def _parse_place(
        self,
        place: dict[str, Any],
        query_lat: float,
        query_lon: float,
    ) -> GooglePlacesFeature | None:
        """
        Parse a single Google Place into our feature format.

        Args:
            place: Place data from Google Places API
            query_lat: Query latitude for distance calculation
            query_lon: Query longitude for distance calculation

        Returns:
            Parsed feature or None if invalid
        """
        try:
            # Extract basic information
            place_id = place.get("place_id", "")
            name = place.get("name", "")
            types = place.get("types", [])

            # Extract location
            geometry = place.get("geometry", {})
            location = geometry.get("location", {})
            lat = location.get("lat")
            lon = location.get("lng")

            if lat is None or lon is None:
                logger.warning(f"Place {name} missing coordinates")
                return None

            # Calculate distance
            distance_km = self._calculate_distance(query_lat, query_lon, lat, lon)

            # Determine category from types
            category = self._determine_category(types)
            subcategory = types[0] if types else None

            # Extract additional metadata
            rating = place.get("rating")
            user_ratings_total = place.get("user_ratings_total")
            price_level = place.get("price_level")
            business_status = place.get("business_status")

            # Create feature
            feature = GooglePlacesFeature(
                google_place_id=place_id,
                name=name,
                types=types,
                centroid=Coordinates(latitude=lat, longitude=lon),
                distance_km=distance_km,
                category=category,
                subcategory=subcategory,
                rating=rating,
                user_ratings_total=user_ratings_total,
                price_level=price_level,
                business_status=business_status,
                vicinity=place.get("vicinity"),
                formatted_address=place.get("formatted_address"),
                icon_url=place.get("icon"),
                photos=place.get("photos", []),
                plus_code=place.get("plus_code"),
                raw_data=place,
            )

            return feature

        except Exception as e:
            logger.warning(f"Error parsing Google Place: {e}")
            return None

    def _determine_category(self, types: list[str]) -> FeatureCategory:
        """
        Determine feature category from Google Place types.

        Args:
            types: List of Google Place types

        Returns:
            Feature category
        """
        # Check each type against our mapping
        for place_type in types:
            if place_type in self.PLACES_TYPE_MAPPING:
                return self.PLACES_TYPE_MAPPING[place_type]

        # Default categorization based on common patterns
        if any(t in ["route", "street_address", "intersection"] for t in types):
            return FeatureCategory.HIGHWAY
        elif any(t in ["political", "locality", "administrative_area"] for t in types):
            return FeatureCategory.OTHER
        else:
            return FeatureCategory.AMENITY  # Most Google Places are amenities

    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Args:
            lat1: First point latitude
            lon1: First point longitude
            lat2: Second point latitude
            lon2: Second point longitude

        Returns:
            Distance in kilometers
        """
        import math

        # Earth radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c
