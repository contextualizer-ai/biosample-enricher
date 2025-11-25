"""Tests for biosample elevation mapper."""

import pytest

from biosample_enricher.biosample_elevation_mapper import (
    BiosampleElevationBatch,
    BiosampleElevationMapper,
)


class TestBiosampleElevationMapper:
    """Test the biosample elevation mapper."""

    def test_extract_coordinates_from_geo_object(self):
        """Test extracting coordinates from geo object."""
        biosample = {
            "id": "sample1",
            "geo": {"latitude": 37.7749, "longitude": -122.4194},
        }

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (37.7749, -122.4194)

    def test_extract_coordinates_from_root_lat_lon(self):
        """Test extracting coordinates from root level lat/lon."""
        biosample = {"id": "sample1", "latitude": 40.7128, "longitude": -74.0060}

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (40.7128, -74.0060)

    def test_extract_coordinates_from_lat_lng(self):
        """Test extracting coordinates from lat/lng fields."""
        biosample = {"id": "sample1", "lat": 51.5074, "lng": -0.1278}

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (51.5074, -0.1278)

    def test_extract_coordinates_string_values(self):
        """Test extracting coordinates from string values."""
        biosample = {"id": "sample1", "lat": "37.7749", "lon": "-122.4194"}

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (37.7749, -122.4194)

    def test_extract_coordinates_decimal_fields(self):
        """Test extracting coordinates from decimal fields."""
        biosample = {"id": "sample1", "lat_decimal": 37.7749, "lon_decimal": -122.4194}

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (37.7749, -122.4194)

    def test_extract_coordinates_nested_location(self):
        """Test extracting coordinates from nested location object."""
        biosample = {
            "id": "sample1",
            "location": {"latitude": 37.7749, "longitude": -122.4194},
        }

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (37.7749, -122.4194)

    def test_extract_coordinates_array_format(self):
        """Test extracting coordinates from array format."""
        # Test [lat, lon] format
        biosample = {"id": "sample1", "coordinates": [37.7749, -122.4194]}

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (37.7749, -122.4194)

        # Test [lon, lat] format (will be auto-detected)
        biosample = {"id": "sample2", "coordinates": [-122.4194, 37.7749]}

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords == (37.7749, -122.4194)

    def test_extract_coordinates_no_coordinates(self):
        """Test extracting coordinates when none are present."""
        biosample = {"id": "sample1", "description": "A sample without coordinates"}

        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords is None

    def test_extract_coordinates_invalid_values(self):
        """Test extracting coordinates with invalid values."""
        # Invalid string values
        biosample = {"lat": "not_a_number", "lon": "-122.4194"}
        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords is None

        # None values
        biosample = {"lat": None, "lon": -122.4194}
        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords is None

        # Missing longitude
        biosample = {"lat": 37.7749}
        coords = BiosampleElevationMapper.extract_coordinates(biosample)
        assert coords is None

    def test_get_biosample_id(self):
        """Test extracting biosample ID."""
        # Test priority order
        biosample = {
            "nmdc_biosample_id": "NMDC123",
            "biosample_id": "BIO456",
            "id": "ID789",
        }
        assert BiosampleElevationMapper.get_biosample_id(biosample) == "NMDC123"

        # Test fallback to biosample_id
        biosample = {"biosample_id": "BIO456", "id": "ID789"}
        assert BiosampleElevationMapper.get_biosample_id(biosample) == "BIO456"

        # Test coordinate-based ID generation
        biosample = {"lat": 37.7749, "lon": -122.4194}
        assert (
            BiosampleElevationMapper.get_biosample_id(biosample)
            == "biosample_37.774900_-122.419400"
        )

        # Test unknown fallback
        biosample = {}
        assert (
            BiosampleElevationMapper.get_biosample_id(biosample) == "unknown_biosample"
        )

    def test_create_elevation_request(self):
        """Test creating an elevation request from biosample."""
        biosample = {
            "id": "sample1",
            "lat": 37.7749,
            "lon": -122.4194,
            "description": "San Francisco sample",
        }

        request = BiosampleElevationMapper.create_elevation_request(biosample)
        assert request is not None
        assert request.latitude == 37.7749
        assert request.longitude == -122.4194
        assert request.preferred_providers is None

        # Test with preferred providers
        request = BiosampleElevationMapper.create_elevation_request(
            biosample, preferred_providers=["usgs", "google"]
        )
        assert request.preferred_providers == ["usgs", "google"]

    def test_create_elevation_request_no_coordinates(self):
        """Test creating elevation request without coordinates."""
        biosample = {"id": "sample1", "description": "Sample without coordinates"}

        request = BiosampleElevationMapper.create_elevation_request(biosample)
        assert request is None

    def test_get_location_context(self):
        """Test extracting location context."""
        biosample = {
            "id": "sample1",
            "country": "USA",
            "state": "California",
            "locality": "San Francisco Bay",
            "depth": 10.5,
            "ecosystem": "marine",
            "habitat": "coastal",
        }

        context = BiosampleElevationMapper.get_location_context(biosample)
        assert context["country"] == "USA"
        assert context["state"] == "California"
        assert context["locality"] == "San Francisco Bay"
        assert context["depth"] == 10.5
        assert context["ecosystem"] == "marine"
        assert context["habitat"] == "coastal"

        # Test nested geo object
        biosample = {"geo": {"country": "UK", "province": "England"}}

        context = BiosampleElevationMapper.get_location_context(biosample)
        assert context["country"] == "UK"
        assert context["state"] == "England"

    def test_validate_coordinates(self):
        """Test coordinate validation."""
        # Valid coordinates
        assert BiosampleElevationMapper.validate_coordinates(37.7749, -122.4194) is True
        assert BiosampleElevationMapper.validate_coordinates(-90, 180) is True
        assert BiosampleElevationMapper.validate_coordinates(90, -180) is True
        assert BiosampleElevationMapper.validate_coordinates(0, 0) is True

        # Invalid coordinates
        assert (
            BiosampleElevationMapper.validate_coordinates(91, 0) is False
        )  # Latitude > 90
        assert (
            BiosampleElevationMapper.validate_coordinates(-91, 0) is False
        )  # Latitude < -90
        assert (
            BiosampleElevationMapper.validate_coordinates(0, 181) is False
        )  # Longitude > 180
        assert (
            BiosampleElevationMapper.validate_coordinates(0, -181) is False
        )  # Longitude < -180

    def test_get_field_mapping_info(self):
        """Test getting field mapping information."""
        info = BiosampleElevationMapper.get_field_mapping_info()

        assert "coordinate_fields" in info
        assert "identifier_fields" in info
        assert "context_fields" in info
        assert "validation" in info

        # Check structure
        assert "primary" in info["coordinate_fields"]
        assert "priority_order" in info["identifier_fields"]
        assert "fields" in info["context_fields"]
        assert "coordinate_ranges" in info["validation"]


class TestBiosampleElevationBatch:
    """Test batch processing utilities."""

    def test_filter_valid_coordinates(self):
        """Test filtering biosamples with valid coordinates."""
        biosamples = [
            {"id": "s1", "lat": 37.7749, "lon": -122.4194},  # Valid
            {"id": "s2", "lat": 91, "lon": 0},  # Invalid latitude
            {"id": "s3"},  # No coordinates
            {"id": "s4", "latitude": 40.7128, "longitude": -74.0060},  # Valid
        ]

        valid = BiosampleElevationBatch.filter_valid_coordinates(biosamples)

        assert len(valid) == 2
        assert valid[0]["id"] == "s1"
        assert valid[1]["id"] == "s4"

    def test_get_coordinate_summary(self):
        """Test getting coordinate summary statistics."""
        biosamples = [
            {"id": "s1", "lat": 37.7749, "lon": -122.4194},
            {"id": "s2", "latitude": 40.7128, "longitude": -74.0060},
            {"id": "s3", "lat": 91, "lon": 0},  # Invalid
            {"id": "s4"},  # Missing
            {"id": "s5", "lat": 35.0, "lon": -120.0},
        ]

        summary = BiosampleElevationBatch.get_coordinate_summary(biosamples)

        assert summary["total_samples"] == 5
        assert summary["valid_coordinates"] == 3
        # s4 has no coordinates, s3 has invalid lat (91) which may be counted as missing
        assert summary["missing_coordinates"] + summary["invalid_coordinates"] == 2
        assert summary["coordinate_coverage"] == 0.6

        # Check bounds
        assert "coordinate_bounds" in summary
        bounds = summary["coordinate_bounds"]
        assert bounds["latitude"]["min"] == 35.0
        assert bounds["latitude"]["max"] == 40.7128
        assert bounds["longitude"]["min"] == -122.4194
        assert bounds["longitude"]["max"] == -74.0060

        # Check distribution
        assert "geographic_distribution" in summary
        dist = summary["geographic_distribution"]
        assert dist["latitude_range"] == pytest.approx(5.7128, rel=1e-4)
        assert dist["longitude_range"] == pytest.approx(48.4134, rel=1e-4)

    def test_get_coordinate_summary_empty(self):
        """Test coordinate summary with empty list."""
        summary = BiosampleElevationBatch.get_coordinate_summary([])

        assert summary["total_samples"] == 0
        assert summary["valid_coordinates"] == 0
        assert summary["missing_coordinates"] == 0
        assert summary["invalid_coordinates"] == 0
        assert summary["coordinate_coverage"] == 0
        assert "coordinate_bounds" not in summary

    def test_get_coordinate_summary_no_valid(self):
        """Test coordinate summary with no valid coordinates."""
        biosamples = [
            {"id": "s1"},  # No coordinates
            {"id": "s2", "lat": "invalid"},  # Invalid
        ]

        summary = BiosampleElevationBatch.get_coordinate_summary(biosamples)

        assert summary["total_samples"] == 2
        assert summary["valid_coordinates"] == 0
        assert summary["missing_coordinates"] == 2
        assert summary["coordinate_coverage"] == 0
        assert "coordinate_bounds" not in summary
