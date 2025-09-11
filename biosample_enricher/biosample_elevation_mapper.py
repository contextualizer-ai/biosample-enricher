#!/usr/bin/env python3
"""
Biosample to Elevation Service Field Mapping

This module provides utilities for mapping between normalized biosample metadata
fields and elevation service inputs, ensuring seamless integration between
biosample data structures and elevation lookup requests.
"""

from typing import Any

from .models import ElevationRequest


class BiosampleElevationMapper:
    """Maps biosample metadata fields to elevation service inputs."""

    @staticmethod
    def extract_coordinates(biosample: dict[str, Any]) -> tuple[float, float] | None:
        """
        Extract latitude and longitude from various biosample field structures.

        Args:
            biosample: Biosample metadata dictionary

        Returns:
            Tuple of (latitude, longitude) or None if not found/invalid
        """
        # Strategy 1: Check for direct geo object (synthetic biosamples format)
        geo = biosample.get("geo", {})
        if isinstance(geo, dict):
            lat = geo.get("latitude")
            lon = geo.get("longitude")
            if lat is not None and lon is not None:
                try:
                    return float(lat), float(lon)
                except (ValueError, TypeError):
                    pass

        # Strategy 2: Check for lat/lon at root level
        lat = biosample.get("latitude") or biosample.get("lat")
        lon = biosample.get("longitude") or biosample.get("lon") or biosample.get("lng")
        if lat is not None and lon is not None:
            try:
                return float(lat), float(lon)
            except (ValueError, TypeError):
                pass

        # Strategy 3: Check for decimal coordinate fields
        lat_decimal = biosample.get("lat_decimal") or biosample.get("latitude_decimal")
        lon_decimal = biosample.get("lon_decimal") or biosample.get("longitude_decimal")
        if lat_decimal is not None and lon_decimal is not None:
            try:
                return float(lat_decimal), float(lon_decimal)
            except (ValueError, TypeError):
                pass

        # Strategy 4: Check for geographic coordinates in various nested structures
        for geo_field in ["geographic_location", "location", "coordinates", "position"]:
            geo_obj = biosample.get(geo_field, {})
            if isinstance(geo_obj, dict):
                lat = geo_obj.get("latitude") or geo_obj.get("lat")
                lon = (
                    geo_obj.get("longitude") or geo_obj.get("lon") or geo_obj.get("lng")
                )
                if lat is not None and lon is not None:
                    try:
                        return float(lat), float(lon)
                    except (ValueError, TypeError):
                        pass

        # Strategy 5: Check for array-like coordinates [lat, lon] or [lon, lat]
        coords = biosample.get("coordinates")
        if isinstance(coords, list | tuple) and len(coords) >= 2:
            try:
                # Assume [lat, lon] format first
                lat, lon = float(coords[0]), float(coords[1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
                # Try [lon, lat] format if first attempt invalid
                lat, lon = float(coords[1]), float(coords[0])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            except (ValueError, TypeError, IndexError):
                pass

        return None

    @staticmethod
    def get_biosample_id(biosample: dict[str, Any]) -> str:
        """
        Extract a unique identifier from biosample metadata.

        Args:
            biosample: Biosample metadata dictionary

        Returns:
            String identifier for the biosample
        """
        # Priority order for ID fields
        id_fields = [
            "nmdc_biosample_id",
            "biosample_id",
            "id",
            "sample_id",
            "name",
            "identifier",
            "accession",
        ]

        for field in id_fields:
            value = biosample.get(field)
            if value:
                return str(value)

        # Fallback: create ID from coordinates if available
        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        if coords:
            lat, lon = coords
            return f"biosample_{lat:.6f}_{lon:.6f}"

        return "unknown_biosample"

    @staticmethod
    def create_elevation_request(
        biosample: dict[str, Any], preferred_providers: list[str] | None = None
    ) -> ElevationRequest | None:
        """
        Create an ElevationRequest from biosample metadata.

        Args:
            biosample: Biosample metadata dictionary
            preferred_providers: Optional list of preferred provider names

        Returns:
            ElevationRequest object or None if coordinates not found
        """
        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        if not coords:
            return None

        lat, lon = coords

        return ElevationRequest(
            latitude=lat, longitude=lon, preferred_providers=preferred_providers
        )

    @staticmethod
    def get_location_context(biosample: dict[str, Any]) -> dict[str, Any]:
        """
        Extract additional location context from biosample metadata.

        Args:
            biosample: Biosample metadata dictionary

        Returns:
            Dictionary with location context information
        """
        context = {}

        # Geographic context fields
        geo_fields = {
            "country": ["country", "nation"],
            "state": ["state", "province", "region"],
            "locality": ["locality", "site", "location_name"],
            "depth": ["depth", "depth_m", "depth_meters"],
            "elevation": ["elevation", "elevation_m", "elevation_meters", "altitude"],
            "ecosystem": ["ecosystem", "ecosystem_category", "env_broad_scale"],
            "habitat": ["habitat", "env_local_scale", "environment"],
        }

        for context_key, field_names in geo_fields.items():
            for field_name in field_names:
                value = biosample.get(field_name)
                if value is not None:
                    context[context_key] = value
                    break

        # Check nested geo object
        geo = biosample.get("geo", {})
        if isinstance(geo, dict):
            for context_key, field_names in geo_fields.items():
                if context_key not in context:
                    for field_name in field_names:
                        value = geo.get(field_name)
                        if value is not None:
                            context[context_key] = value
                            break

        return context

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """
        Validate that coordinates are within valid ranges.

        Args:
            lat: Latitude value
            lon: Longitude value

        Returns:
            True if coordinates are valid, False otherwise
        """
        return -90 <= lat <= 90 and -180 <= lon <= 180

    @staticmethod
    def get_field_mapping_info() -> dict[str, Any]:
        """
        Get comprehensive information about biosample field mappings.

        Returns:
            Dictionary with mapping information and examples
        """
        return {
            "coordinate_fields": {
                "primary": {
                    "description": "Primary coordinate extraction strategies",
                    "strategies": [
                        {
                            "name": "geo_object",
                            "fields": ["geo.latitude", "geo.longitude"],
                            "example": {
                                "geo": {"latitude": 43.8791, "longitude": -103.4591}
                            },
                        },
                        {
                            "name": "root_level",
                            "fields": ["latitude", "longitude", "lat", "lon", "lng"],
                            "example": {"latitude": 43.8791, "longitude": -103.4591},
                        },
                        {
                            "name": "decimal_coords",
                            "fields": [
                                "lat_decimal",
                                "lon_decimal",
                                "latitude_decimal",
                                "longitude_decimal",
                            ],
                            "example": {
                                "lat_decimal": 43.8791,
                                "lon_decimal": -103.4591,
                            },
                        },
                    ],
                },
                "nested": {
                    "description": "Nested coordinate extraction strategies",
                    "fields": [
                        "geographic_location.latitude",
                        "location.latitude",
                        "coordinates.latitude",
                        "position.latitude",
                    ],
                    "example": {
                        "geographic_location": {
                            "latitude": 43.8791,
                            "longitude": -103.4591,
                        }
                    },
                },
                "array_format": {
                    "description": "Array-based coordinate formats",
                    "formats": [
                        {
                            "name": "lat_lon_array",
                            "example": {"coordinates": [43.8791, -103.4591]},
                        },
                        {
                            "name": "lon_lat_array",
                            "example": {"coordinates": [-103.4591, 43.8791]},
                        },
                    ],
                    "note": "Automatic detection based on valid coordinate ranges",
                },
            },
            "identifier_fields": {
                "description": "Biosample identifier extraction priority order",
                "priority_order": [
                    "nmdc_biosample_id",
                    "biosample_id",
                    "id",
                    "sample_id",
                    "name",
                    "identifier",
                    "accession",
                ],
                "fallback": "Generated from coordinates: biosample_{lat:.6f}_{lon:.6f}",
            },
            "context_fields": {
                "description": "Additional location context extraction",
                "fields": {
                    "country": ["country", "nation"],
                    "state": ["state", "province", "region"],
                    "locality": ["locality", "site", "location_name"],
                    "depth": ["depth", "depth_m", "depth_meters"],
                    "existing_elevation": [
                        "elevation",
                        "elevation_m",
                        "elevation_meters",
                        "altitude",
                    ],
                    "ecosystem": ["ecosystem", "ecosystem_category", "env_broad_scale"],
                    "habitat": ["habitat", "env_local_scale", "environment"],
                },
            },
            "validation": {
                "coordinate_ranges": {
                    "latitude": {"min": -90, "max": 90},
                    "longitude": {"min": -180, "max": 180},
                },
                "type_conversion": (
                    "Automatic string to float conversion with error handling"
                ),
            },
        }


class BiosampleElevationBatch:
    """Utilities for batch processing biosamples with elevation lookups."""

    @staticmethod
    def filter_valid_coordinates(
        biosamples: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Filter biosamples to only those with valid coordinates.

        Args:
            biosamples: List of biosample metadata dictionaries

        Returns:
            List of biosamples with valid coordinates
        """
        valid_samples = []

        for biosample in biosamples:
            coords = BiosampleElevationMapper.extract_coordinates(biosample)
            if coords and BiosampleElevationMapper.validate_coordinates(*coords):
                valid_samples.append(biosample)

        return valid_samples

    @staticmethod
    def get_coordinate_summary(biosamples: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Get summary statistics about coordinates in a biosample collection.

        Args:
            biosamples: List of biosample metadata dictionaries

        Returns:
            Dictionary with coordinate statistics
        """
        total_samples = len(biosamples)
        valid_coords: list[tuple[float, float]] = []
        missing_coords = 0
        invalid_coords = 0

        for biosample in biosamples:
            coords = BiosampleElevationMapper.extract_coordinates(biosample)
            if coords:
                lat, lon = coords
                if BiosampleElevationMapper.validate_coordinates(lat, lon):
                    valid_coords.append((lat, lon))
                else:
                    invalid_coords += 1
            else:
                missing_coords += 1

        summary: dict[str, Any] = {
            "total_samples": total_samples,
            "valid_coordinates": len(valid_coords),
            "missing_coordinates": missing_coords,
            "invalid_coordinates": invalid_coords,
            "coordinate_coverage": len(valid_coords) / total_samples
            if total_samples > 0
            else 0,
        }

        if valid_coords:
            lats = [coord[0] for coord in valid_coords]
            lons = [coord[1] for coord in valid_coords]

            lat_bounds = {"min": min(lats), "max": max(lats)}
            lon_bounds = {"min": min(lons), "max": max(lons)}

            summary["coordinate_bounds"] = {
                "latitude": lat_bounds,
                "longitude": lon_bounds,
            }

            summary["geographic_distribution"] = {
                "latitude_range": max(lats) - min(lats),
                "longitude_range": max(lons) - min(lons),
            }

        return summary


# Example usage and testing utilities
def demonstrate_field_mapping() -> None:
    """Demonstrate the field mapping capabilities with example data."""

    # Example biosample formats
    test_biosamples: list[dict[str, Any]] = [
        {
            "nmdc_biosample_id": "SAMN123456",
            "name": "Forest soil sample",
            "geo": {"latitude": 43.8791, "longitude": -103.4591, "country": "USA"},
            "ecosystem_category": "terrestrial",
        },
        {
            "biosample_id": "GOLD456789",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "country": "United Kingdom",
            "site": "London urban soil",
        },
        {
            "id": "sample_001",
            "coordinates": [37.7749, -122.4194],
            "locality": "San Francisco Bay",
            "depth_m": 2.5,
        },
        {"name": "Invalid sample", "description": "No coordinates available"},
    ]

    mapper = BiosampleElevationMapper()

    print("=== Biosample Field Mapping Demonstration ===\n")

    for i, biosample in enumerate(test_biosamples, 1):
        print(f"Sample {i}: {biosample.get('name', biosample.get('id', 'Unknown'))}")

        # Extract coordinates
        coords = mapper.extract_coordinates(biosample)
        print(f"  Coordinates: {coords}")

        # Get sample ID
        sample_id = mapper.get_biosample_id(biosample)
        print(f"  Sample ID: {sample_id}")

        # Get location context
        context = mapper.get_location_context(biosample)
        print(f"  Context: {context}")

        # Create elevation request
        request = mapper.create_elevation_request(biosample)
        print(f"  Elevation Request: {request}")

        print()

    # Batch summary
    BiosampleElevationBatch.filter_valid_coordinates(test_biosamples)
    summary = BiosampleElevationBatch.get_coordinate_summary(test_biosamples)

    print("=== Batch Summary ===")
    print(f"Total samples: {summary['total_samples']}")
    print(f"Valid coordinates: {summary['valid_coordinates']}")
    print(f"Coverage: {summary['coordinate_coverage']:.1%}")

    if "coordinate_bounds" in summary:
        bounds = summary["coordinate_bounds"]
        print(
            f"Latitude range: {bounds['latitude']['min']:.4f} to "
            f"{bounds['latitude']['max']:.4f}"
        )
        print(
            f"Longitude range: {bounds['longitude']['min']:.4f} to "
            f"{bounds['longitude']['max']:.4f}"
        )


if __name__ == "__main__":
    demonstrate_field_mapping()
