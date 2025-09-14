"""Data models for OpenStreetMap geographic features."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OSMElementType(str, Enum):
    """Types of OSM elements."""

    NODE = "node"
    WAY = "way"
    RELATION = "relation"


class GeometryType(str, Enum):
    """Types of geometric representations."""

    POINT = "point"
    LINESTRING = "linestring"
    POLYGON = "polygon"
    MULTIPOLYGON = "multipolygon"


class FeatureCategory(str, Enum):
    """Main categories of OSM features."""

    NATURAL = "natural"
    WATERWAY = "waterway"
    HIGHWAY = "highway"
    RAILWAY = "railway"
    AEROWAY = "aeroway"
    AMENITY = "amenity"
    LEISURE = "leisure"
    LANDUSE = "landuse"
    BUILDING = "building"
    BOUNDARY = "boundary"
    PLACE = "place"
    TOURISM = "tourism"
    SHOP = "shop"
    CRAFT = "craft"
    OFFICE = "office"
    OTHER = "other"


class Coordinates(BaseModel):
    """Geographic coordinates."""

    latitude: float = Field(ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(ge=-180, le=180, description="Longitude coordinate")


class OSMNamedFeature(BaseModel):
    """A named geographic feature from OpenStreetMap."""

    # OSM identifiers
    osm_type: OSMElementType = Field(description="Type of OSM element")
    osm_id: int = Field(description="OSM element ID")

    # Names and identification
    name: str | None = Field(default=None, description="Primary name of the feature")
    alt_names: list[str] = Field(default_factory=list, description="Alternative names")
    wikidata_id: str | None = Field(default=None, description="Wikidata identifier")
    wikipedia: str | None = Field(default=None, description="Wikipedia reference")

    # Geographic properties
    centroid: Coordinates | None = Field(
        default=None, description="Center point of the feature"
    )
    distance_km: float | None = Field(
        default=None, ge=0.0, description="Distance from query point in kilometers"
    )
    geometry_type: GeometryType | None = Field(
        default=None, description="Type of geometry"
    )

    # Categorization
    category: FeatureCategory = Field(
        default=FeatureCategory.OTHER, description="Main feature category"
    )
    subcategory: str | None = Field(
        default=None, description="Specific feature type within category"
    )

    # All OSM tags
    tags: dict[str, str] = Field(
        default_factory=dict, description="Complete OSM tag set"
    )

    # Quality indicators
    importance: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Feature importance score"
    )


class OSMUnnamedCounts(BaseModel):
    """Counts of unnamed features by category and subcategory."""

    key: str = Field(description="OSM tag key (e.g., 'natural', 'highway')")
    total_count: int = Field(ge=0, description="Total features with this key")
    value_counts: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Counts by tag value and element type: {value: {node: X, way: Y, relation: Z}}",
    )


class OSMQuery(BaseModel):
    """Parameters for an OSM Overpass query."""

    center: Coordinates = Field(description="Center point of search")
    radius_m: int = Field(ge=1, le=50000, description="Search radius in meters")
    timeout_s: int = Field(ge=1, le=600, description="Query timeout in seconds")


class OSMFeaturesResult(BaseModel):
    """Complete result from OSM features enrichment."""

    # Query information
    query: OSMQuery = Field(description="Query parameters used")

    # Results
    named_features: list[OSMNamedFeature] = Field(
        default_factory=list, description="Named features ordered by distance"
    )
    unnamed_counts: list[OSMUnnamedCounts] = Field(
        default_factory=list, description="Counts of unnamed features by category"
    )

    # Summary statistics
    total_elements: int = Field(ge=0, description="Total OSM elements found")
    named_features_count: int = Field(ge=0, description="Number of named features")
    unnamed_categories_count: int = Field(
        ge=0, description="Number of unnamed feature categories"
    )
    total_unnamed_count: int = Field(ge=0, description="Total unnamed features")

    # Quality and provenance
    success: bool = Field(default=True, description="Whether query succeeded")
    error_message: str | None = Field(
        default=None, description="Error details if failed"
    )
    response_time_ms: float | None = Field(
        default=None, description="Query response time in milliseconds"
    )
    data_source: str = Field(
        default="OpenStreetMap Overpass API", description="Data source"
    )
    query_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Query execution time"
    )

    def get_features_by_category(
        self, category: FeatureCategory
    ) -> list[OSMNamedFeature]:
        """Get all named features of a specific category."""
        return [f for f in self.named_features if f.category == category]

    def get_nearest_feature(self, category: FeatureCategory) -> OSMNamedFeature | None:
        """Get the nearest named feature of a specific category."""
        category_features = self.get_features_by_category(category)
        if not category_features:
            return None
        return min(
            category_features,
            key=lambda f: f.distance_km if f.distance_km is not None else float("inf"),
        )

    def get_feature_counts_by_category(self) -> dict[str, int]:
        """Get counts of unnamed features by main category."""
        counts = {}
        for unnamed_group in self.unnamed_counts:
            counts[unnamed_group.key] = unnamed_group.total_count
        return counts

    def get_distance_summary(self) -> dict[str, Any]:
        """Generate distance summary for key feature categories."""
        summary = {}

        # Key categories for distance analysis
        key_categories = [
            FeatureCategory.NATURAL,
            FeatureCategory.WATERWAY,
            FeatureCategory.HIGHWAY,
            FeatureCategory.AMENITY,
            FeatureCategory.BUILDING,
        ]

        for category in key_categories:
            features = self.get_features_by_category(category)
            if features:
                distances = [
                    f.distance_km for f in features if f.distance_km is not None
                ]
                if distances:
                    summary[f"nearest_{category.value}_km"] = min(distances)
                    summary[f"avg_{category.value}_km"] = sum(distances) / len(
                        distances
                    )
                    summary[f"{category.value}_within_1km"] = len(
                        [d for d in distances if d <= 1.0]
                    )
                else:
                    summary[f"nearest_{category.value}_km"] = 0.0
                    summary[f"{category.value}_within_1km"] = 0
            else:
                summary[f"nearest_{category.value}_km"] = 0.0
                summary[f"{category.value}_within_1km"] = 0

        return summary

    def to_enrichment_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for biosample enrichment."""
        enrichment: dict[str, Any] = {
            "osm_features_found": len(self.named_features),
            "osm_categories_found": self.unnamed_categories_count,
            "osm_total_elements": self.total_elements,
            "osm_query_radius_m": self.query.radius_m,
        }

        # Add distance summary
        distance_summary = self.get_distance_summary()
        enrichment.update(distance_summary)

        # Add nearest features for key categories
        key_categories = [
            FeatureCategory.NATURAL,
            FeatureCategory.WATERWAY,
            FeatureCategory.HIGHWAY,
            FeatureCategory.AMENITY,
        ]

        for category in key_categories:
            nearest = self.get_nearest_feature(category)
            if nearest:
                enrichment[f"nearest_{category.value}_name"] = nearest.name or ""
                enrichment[f"nearest_{category.value}_type"] = nearest.subcategory or ""
                enrichment[f"nearest_{category.value}_distance_km"] = (
                    nearest.distance_km or 0.0
                )

        # Add feature counts by category
        category_counts = self.get_feature_counts_by_category()
        for category_name, count in category_counts.items():
            enrichment[f"osm_{category_name}_count"] = count

        # Provider information
        enrichment["osm_data_source"] = self.data_source
        enrichment["osm_query_timestamp"] = self.query_timestamp.isoformat()

        return enrichment


class OSMFetchResult(BaseModel):
    """Internal result from OSM Overpass API fetch operation."""

    ok: bool = Field(description="Whether fetch was successful")
    result: OSMFeaturesResult | None = Field(
        default=None, description="OSM features result"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    raw: dict[str, Any] = Field(
        default_factory=dict, description="Raw Overpass API response"
    )


# Google Places API Models


class GooglePlacesFeature(BaseModel):
    """A feature from Google Places API."""

    google_place_id: str = Field(description="Google Place ID")
    name: str | None = Field(default=None, description="Feature name")
    types: list[str] = Field(default_factory=list, description="Google Place types")
    centroid: Coordinates | None = Field(
        default=None, description="Feature center point"
    )
    distance_km: float | None = Field(
        default=None, ge=0.0, description="Distance from query point in kilometers"
    )
    category: FeatureCategory = Field(
        default=FeatureCategory.OTHER, description="Mapped feature category"
    )
    subcategory: str | None = Field(
        default=None, description="Primary Google Place type"
    )

    # Google Places specific fields
    rating: float | None = Field(
        default=None, ge=0.0, le=5.0, description="Average rating"
    )
    user_ratings_total: int | None = Field(
        default=None, ge=0, description="Total number of ratings"
    )
    price_level: int | None = Field(
        default=None, ge=0, le=4, description="Price level (0-4)"
    )
    business_status: str | None = Field(
        default=None, description="Business operational status"
    )
    vicinity: str | None = Field(default=None, description="Simplified address")
    formatted_address: str | None = Field(
        default=None, description="Full formatted address"
    )
    icon_url: str | None = Field(default=None, description="URL to category icon")
    photos: list[dict[str, Any]] = Field(
        default_factory=list, description="Photo references"
    )
    plus_code: dict[str, Any] | None = Field(
        default=None, description="Plus code information"
    )
    raw_data: dict[str, Any] = Field(
        default_factory=dict, description="Raw Google Places data"
    )


class GooglePlacesResult(BaseModel):
    """Result from Google Places API query."""

    query: Coordinates = Field(description="Query coordinates")
    radius_m: int = Field(description="Search radius in meters")
    named_features: list[GooglePlacesFeature] = Field(
        default_factory=list, description="Named features found"
    )
    unnamed_counts: list[dict[str, Any]] = Field(
        default_factory=list, description="Counts by category"
    )
    total_features: int = Field(default=0, ge=0, description="Total features found")
    success: bool = Field(default=False, description="Whether query was successful")
    provider: str = Field(default="google_places", description="Provider identifier")
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )

    def to_enrichment_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for biosample enrichment."""
        enrichment: dict[str, Any] = {
            "google_places_found": len(self.named_features),
            "google_total_features": self.total_features,
            "google_query_radius_m": self.radius_m,
            "google_enrichment_success": self.success,
        }

        # Add nearest features for key categories
        key_categories = [
            FeatureCategory.NATURAL,
            FeatureCategory.AMENITY,
            FeatureCategory.HIGHWAY,
            FeatureCategory.BUILDING,
        ]

        for category in key_categories:
            nearest = self.get_nearest_feature(category)
            if nearest:
                enrichment[f"google_nearest_{category.value}_name"] = nearest.name or ""
                enrichment[f"google_nearest_{category.value}_type"] = (
                    nearest.subcategory or ""
                )
                enrichment[f"google_nearest_{category.value}_distance_km"] = float(
                    nearest.distance_km or 0.0
                )
                enrichment[f"google_nearest_{category.value}_rating"] = float(
                    nearest.rating or 0.0
                )

        # Add feature counts by category
        category_counts: dict[str, int] = {}
        for feature in self.named_features:
            category_value = feature.category.value
            category_counts[category_value] = category_counts.get(category_value, 0) + 1

        for category_name, count in category_counts.items():
            enrichment[f"google_{category_name}_count"] = count

        return enrichment

    def get_nearest_feature(
        self, category: FeatureCategory
    ) -> GooglePlacesFeature | None:
        """Get nearest feature of specified category."""
        category_features = [f for f in self.named_features if f.category == category]
        if not category_features:
            return None

        # Sort by distance and return nearest
        category_features.sort(key=lambda f: f.distance_km or float("inf"))
        return category_features[0]


class GooglePlacesFetchResult(BaseModel):
    """Result of fetching from Google Places API."""

    ok: bool = Field(description="Whether the fetch was successful")
    result: GooglePlacesResult | None = Field(
        default=None, description="Parsed result if successful"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    raw: dict[str, Any] = Field(default_factory=dict, description="Raw API response")


# Combined Results Model


class CombinedFeaturesResult(BaseModel):
    """Combined results from multiple geographic feature providers."""

    query: Coordinates = Field(description="Query coordinates")
    radius_m: int = Field(description="Search radius in meters")
    osm_result: OSMFeaturesResult | None = Field(
        default=None, description="OSM features result"
    )
    google_result: GooglePlacesResult | None = Field(
        default=None, description="Google Places result"
    )
    providers_successful: list[str] = Field(
        default_factory=list, description="List of successful providers"
    )
    providers_failed: list[str] = Field(
        default_factory=list, description="List of failed providers"
    )
    combined_enrichment_success: bool = Field(
        default=False, description="Whether any provider succeeded"
    )

    def to_enrichment_dict(self) -> dict[str, Any]:
        """Convert combined results to enrichment dictionary."""
        enrichment: dict[str, Any] = {
            "features_query_radius_m": self.radius_m,
            "features_providers_successful": self.providers_successful,
            "features_providers_failed": self.providers_failed,
            "features_enrichment_success": self.combined_enrichment_success,
        }

        # Add OSM enrichment data
        if self.osm_result:
            osm_enrichment = self.osm_result.to_enrichment_dict()
            enrichment.update(osm_enrichment)

        # Add Google Places enrichment data
        if self.google_result:
            google_enrichment = self.google_result.to_enrichment_dict()
            enrichment.update(google_enrichment)

        # Calculate combined statistics
        total_named_features = 0
        if self.osm_result:
            total_named_features += len(self.osm_result.named_features)
        if self.google_result:
            total_named_features += len(self.google_result.named_features)

        enrichment["features_total_named_combined"] = total_named_features

        return enrichment
