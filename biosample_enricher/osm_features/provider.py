"""OpenStreetMap Overpass API provider for geographic features."""

import math
import time
from typing import Any

from biosample_enricher.http_cache import get_session
from biosample_enricher.logging_config import get_logger
from biosample_enricher.osm_features.models import (
    Coordinates,
    FeatureCategory,
    GeometryType,
    OSMElementType,
    OSMFeaturesResult,
    OSMFetchResult,
    OSMNamedFeature,
    OSMQuery,
    OSMUnnamedCounts,
)

logger = get_logger(__name__)


class OSMOverpassProvider:
    """OpenStreetMap Overpass API provider for geographic features."""

    def __init__(self, base_url: str = "https://overpass-api.de/api/interpreter"):
        """Initialize OSM Overpass provider."""
        self.base_url = base_url
        self._session = get_session()
        self._last_request_time = 0.0
        self._min_request_interval = 1.0  # 1 second between requests (Overpass policy)

    def is_available(self) -> bool:
        """Check if Overpass API is available."""
        try:
            # Simple status check with a minimal query
            test_query = "[out:json][timeout:5]; node(1); out;"
            response = self._session.post(self.base_url, data=test_query, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_features(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 1000,
        timeout_s: int = 180,
    ) -> OSMFetchResult:
        """Get geographic features around a location."""
        # Validate inputs
        if not (-90 <= latitude <= 90):
            return OSMFetchResult(
                ok=False, error=f"Invalid latitude: {latitude}", raw={}
            )

        if not (-180 <= longitude <= 180):
            return OSMFetchResult(
                ok=False, error=f"Invalid longitude: {longitude}", raw={}
            )

        if not (1 <= radius_m <= 50000):
            return OSMFetchResult(
                ok=False, error=f"Invalid radius: {radius_m} (must be 1-50000m)", raw={}
            )

        # Rate limiting
        self._enforce_rate_limit()

        try:
            start_time = time.time()

            # Comprehensive Overpass query for all features
            query = f"""
            [out:json][timeout:{timeout_s}];
            (
              node(around:{radius_m},{latitude},{longitude});
              way(around:{radius_m},{latitude},{longitude});
              relation(around:{radius_m},{latitude},{longitude});
            );
            out body geom qt;
            """

            logger.info(
                f"Querying OSM Overpass API for features within {radius_m}m of {latitude}, {longitude}"
            )

            response = self._session.post(
                self.base_url, data=query, timeout=timeout_s + 10
            )

            response_time = (time.time() - start_time) * 1000

            if response.status_code != 200:
                return OSMFetchResult(
                    ok=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    raw={"status_code": response.status_code, "text": response.text},
                )

            data = response.json()

            # Check for Overpass API errors
            if "remark" in data:
                return OSMFetchResult(
                    ok=False,
                    error=f"Overpass API error: {data['remark']}",
                    raw=data,
                )

            elements = data.get("elements", [])
            logger.info(f"Retrieved {len(elements)} OSM elements")

            # Parse the results
            result = self._parse_overpass_response(
                data, latitude, longitude, radius_m, timeout_s, response_time
            )

            return OSMFetchResult(ok=True, result=result, raw=data)

        except Exception as e:
            logger.error(f"OSM Overpass query failed: {e}")
            return OSMFetchResult(ok=False, error=str(e), raw={})

    def _enforce_rate_limit(self) -> None:
        """Enforce Overpass API rate limiting policy."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _parse_overpass_response(
        self,
        data: dict[str, Any],
        query_lat: float,
        query_lon: float,
        radius_m: int,
        timeout_s: int,
        response_time_ms: float,
    ) -> OSMFeaturesResult:
        """Parse Overpass API response into structured format."""
        elements = data.get("elements", [])

        named_features = []
        unnamed_counts_dict: dict[str, dict[str, Any]] = {}

        for element in elements:
            tags = element.get("tags", {})
            if not tags:  # Skip elements without tags
                continue

            osm_type = OSMElementType(element.get("type", "node"))
            osm_id = element.get("id", 0)

            # Calculate distance and centroid
            distance_km = self._calculate_feature_distance(
                query_lat, query_lon, element
            )
            centroid = self._get_element_centroid(element)

            if self._is_named_feature(tags):
                # Named feature - store complete information
                feature = self._create_named_feature(
                    element, tags, osm_type, osm_id, distance_km, centroid
                )
                named_features.append(feature)
            else:
                # Unnamed feature - add to counts
                self._add_to_unnamed_counts(unnamed_counts_dict, tags, osm_type)

        # Convert unnamed counts to structured format
        unnamed_counts = [
            OSMUnnamedCounts(
                key=key,
                total_count=counts.get("_total", 0),
                value_counts={k: v for k, v in counts.items() if k != "_total"},
            )
            for key, counts in unnamed_counts_dict.items()
        ]

        # Sort named features by distance
        named_features.sort(
            key=lambda x: x.distance_km if x.distance_km is not None else float("inf")
        )

        return OSMFeaturesResult(
            query=OSMQuery(
                center=Coordinates(latitude=query_lat, longitude=query_lon),
                radius_m=radius_m,
                timeout_s=timeout_s,
            ),
            named_features=named_features,
            unnamed_counts=unnamed_counts,
            total_elements=len(elements),
            named_features_count=len(named_features),
            unnamed_categories_count=len(unnamed_counts),
            total_unnamed_count=sum(uc.total_count for uc in unnamed_counts),
            response_time_ms=response_time_ms,
        )

    def _is_named_feature(self, tags: dict[str, str]) -> bool:
        """Check if feature has naming tags."""
        name_tags = [
            "name",
            "official_name",
            "alt_name",
            "wikidata",
            "wikipedia",
            "short_name",
        ]
        return any(tag in tags for tag in name_tags)

    def _create_named_feature(
        self,
        element: dict[str, Any],
        tags: dict[str, str],
        osm_type: OSMElementType,
        osm_id: int,
        distance_km: float | None,
        centroid: Coordinates | None,
    ) -> OSMNamedFeature:
        """Create a named feature from OSM element."""
        # Extract names
        name = (
            tags.get("name")
            or tags.get("official_name")
            or tags.get("alt_name")
            or tags.get("short_name")
        )

        alt_names = []
        for name_tag in ["alt_name", "name:en", "name:local"]:
            if name_tag in tags and tags[name_tag] != name:
                alt_names.append(tags[name_tag])

        # Determine category and subcategory
        category, subcategory = self._categorize_feature(tags)

        # Determine geometry type
        geometry_type = self._determine_geometry_type(element, tags)

        return OSMNamedFeature(
            osm_type=osm_type,
            osm_id=osm_id,
            name=name,
            alt_names=alt_names,
            wikidata_id=tags.get("wikidata"),
            wikipedia=tags.get("wikipedia"),
            centroid=centroid,
            distance_km=distance_km,
            geometry_type=geometry_type,
            category=category,
            subcategory=subcategory,
            tags=tags,
        )

    def _categorize_feature(
        self, tags: dict[str, str]
    ) -> tuple[FeatureCategory, str | None]:
        """Categorize OSM feature based on tags."""
        # Priority order for categorization
        category_mappings = {
            "natural": FeatureCategory.NATURAL,
            "waterway": FeatureCategory.WATERWAY,
            "highway": FeatureCategory.HIGHWAY,
            "railway": FeatureCategory.RAILWAY,
            "aeroway": FeatureCategory.AEROWAY,
            "amenity": FeatureCategory.AMENITY,
            "leisure": FeatureCategory.LEISURE,
            "landuse": FeatureCategory.LANDUSE,
            "building": FeatureCategory.BUILDING,
            "boundary": FeatureCategory.BOUNDARY,
            "place": FeatureCategory.PLACE,
            "tourism": FeatureCategory.TOURISM,
            "shop": FeatureCategory.SHOP,
            "craft": FeatureCategory.CRAFT,
            "office": FeatureCategory.OFFICE,
        }

        for tag_key, category in category_mappings.items():
            if tag_key in tags:
                return category, tags[tag_key]

        return FeatureCategory.OTHER, None

    def _determine_geometry_type(
        self, element: dict[str, Any], tags: dict[str, str]
    ) -> GeometryType | None:
        """Determine geometry type from OSM element."""
        elem_type = element.get("type")

        if elem_type == "node":
            return GeometryType.POINT
        elif elem_type == "way":
            # Check if it's a closed way (polygon)
            geometry = element.get("geometry", [])
            if (
                len(geometry) > 3
                and geometry[0] == geometry[-1]
                or tags.get("area") == "yes"
            ):
                return GeometryType.POLYGON
            else:
                return GeometryType.LINESTRING
        elif elem_type == "relation":
            if tags.get("type") == "multipolygon":
                return GeometryType.MULTIPOLYGON
            else:
                return GeometryType.POLYGON

        return None

    def _add_to_unnamed_counts(
        self,
        counts_dict: dict[str, Any],
        tags: dict[str, str],
        osm_type: OSMElementType,
    ) -> None:
        """Add element to unnamed feature counts."""
        for key, value in tags.items():
            if key not in counts_dict:
                counts_dict[key] = {"_total": 0}

            counts_dict[key]["_total"] += 1

            if value not in counts_dict[key]:
                counts_dict[key][value] = {"node": 0, "way": 0, "relation": 0}

            counts_dict[key][value][osm_type.value] += 1

    def _get_element_centroid(self, element: dict[str, Any]) -> Coordinates | None:
        """Extract centroid coordinates from OSM element."""
        if element.get("type") == "node":
            lat = element.get("lat")
            lon = element.get("lon")
            if lat is not None and lon is not None:
                return Coordinates(latitude=lat, longitude=lon)

        elif "center" in element:
            center = element["center"]
            lat = center.get("lat")
            lon = center.get("lon")
            if lat is not None and lon is not None:
                return Coordinates(latitude=lat, longitude=lon)

        elif element.get("type") == "way" and "geometry" in element:
            # Calculate centroid of way
            coords = [
                (node["lat"], node["lon"])
                for node in element["geometry"]
                if "lat" in node and "lon" in node
            ]
            if coords:
                avg_lat = sum(lat for lat, lon in coords) / len(coords)
                avg_lon = sum(lon for lat, lon in coords) / len(coords)
                return Coordinates(latitude=avg_lat, longitude=avg_lon)

        elif element.get("type") == "relation" and "members" in element:
            # For relations, try to get centroid from member geometry
            all_coords = []
            for member in element["members"]:
                if "geometry" in member:
                    for node in member["geometry"]:
                        if "lat" in node and "lon" in node:
                            all_coords.append((node["lat"], node["lon"]))

            if all_coords:
                avg_lat = sum(lat for lat, lon in all_coords) / len(all_coords)
                avg_lon = sum(lon for lat, lon in all_coords) / len(all_coords)
                return Coordinates(latitude=avg_lat, longitude=avg_lon)

        return None

    def _calculate_feature_distance(
        self, sample_lat: float, sample_lon: float, element: dict[str, Any]
    ) -> float | None:
        """Calculate distance from sample point to OSM feature geometry."""
        elem_type = element.get("type")

        if elem_type == "node":
            lat = element.get("lat")
            lon = element.get("lon")
            if lat is not None and lon is not None:
                return self._haversine_km(sample_lat, sample_lon, lat, lon)

        elif elem_type == "way" and "geometry" in element:
            coords = [
                (node["lat"], node["lon"])
                for node in element["geometry"]
                if "lat" in node and "lon" in node
            ]
            if coords:
                tags = element.get("tags", {})
                # Check if this is a closed way (polygon)
                if (len(coords) > 3 and coords[0] == coords[-1]) or tags.get(
                    "area"
                ) == "yes":
                    return self._distance_point_to_polygon_km(
                        sample_lat, sample_lon, coords
                    )
                else:
                    return self._distance_point_to_linestring_km(
                        sample_lat, sample_lon, coords
                    )

        # Fallback to centroid distance
        centroid = self._get_element_centroid(element)
        if centroid:
            return self._haversine_km(
                sample_lat, sample_lon, centroid.latitude, centroid.longitude
            )

        return None

    def _haversine_km(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate haversine distance between two points in kilometers."""
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def _distance_point_to_linestring_km(
        self, point_lat: float, point_lon: float, linestring: list[tuple[float, float]]
    ) -> float:
        """Calculate minimum distance from point to linestring in kilometers."""
        if not linestring:
            return float("inf")

        min_distance = float("inf")

        for i in range(len(linestring) - 1):
            # Get line segment
            lat1, lon1 = linestring[i]
            lat2, lon2 = linestring[i + 1]

            # Distance to endpoints
            dist1 = self._haversine_km(point_lat, point_lon, lat1, lon1)
            dist2 = self._haversine_km(point_lat, point_lon, lat2, lon2)
            min_distance = min(min_distance, dist1, dist2)

        return min_distance

    def _distance_point_to_polygon_km(
        self, point_lat: float, point_lon: float, polygon: list[tuple[float, float]]
    ) -> float:
        """Calculate distance from point to polygon in kilometers (0 if within)."""
        if not polygon:
            return float("inf")

        # Simple point-in-polygon check using ray casting
        x, y = point_lon, point_lat
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y

        if inside:
            return 0.0

        # If outside, calculate distance to edge
        return self._distance_point_to_linestring_km(point_lat, point_lon, polygon)
