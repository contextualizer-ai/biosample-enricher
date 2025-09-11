#!/usr/bin/env python3
"""
Comprehensive tests for the elevation service.

Live integration tests for coordinate classification, provider implementations,
service orchestration, and output formatting.
"""

import os

import pytest

from biosample_enricher.elevation.classifier import CoordinateClassifier
from biosample_enricher.elevation.providers import (
    GoogleElevationProvider,
    OpenTopoDataProvider,
    OSMElevationProvider,
    USGSElevationProvider,
)
from biosample_enricher.elevation.service import ElevationService
from biosample_enricher.elevation.utils import calculate_distance_m
from biosample_enricher.models import (
    CoordinateClassification,
    ElevationRequest,
    FetchResult,
    GeoPoint,
    ValueStatus,
)


class TestCoordinateClassifier:
    """Test the coordinate classification system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = CoordinateClassifier()

    def test_classify_conus(self):
        """Test classification of Continental US coordinates."""
        # San Francisco, CA
        result = self.classifier.classify(37.7749, -122.4194)

        assert result.is_us_territory is True
        assert result.region == "CONUS"
        assert result.confidence >= 0.9

    def test_classify_alaska(self):
        """Test classification of Alaska coordinates."""
        # Anchorage, AK
        result = self.classifier.classify(61.2181, -149.9003)

        assert result.is_us_territory is True
        assert result.region == "AK"
        assert result.confidence >= 0.9

    def test_classify_hawaii(self):
        """Test classification of Hawaii coordinates."""
        # Honolulu, HI
        result = self.classifier.classify(21.3099, -157.8581)

        assert result.is_us_territory is True
        assert result.region == "HI"
        assert result.confidence >= 0.9

    def test_classify_puerto_rico(self):
        """Test classification of Puerto Rico coordinates."""
        # San Juan, PR
        result = self.classifier.classify(18.4655, -66.1057)

        assert result.is_us_territory is True
        assert result.region == "PR"
        assert result.confidence >= 0.9

    def test_classify_guam(self):
        """Test classification of Guam coordinates."""
        # Hagåtña, Guam
        result = self.classifier.classify(13.4443, 144.7937)

        assert result.is_us_territory is True
        assert result.region == "GU"
        assert result.confidence >= 0.9

    def test_classify_non_us(self):
        """Test classification of non-US coordinates."""
        # London, UK
        result = self.classifier.classify(51.5074, -0.1278)

        assert result.is_us_territory is False
        assert result.region is None
        assert result.confidence >= 0.9

    def test_classify_boundary_cases(self):
        """Test coordinates near US boundaries."""
        # Just outside CONUS boundary
        result = self.classifier.classify(24.0, -125.5)  # South of CONUS
        assert result.is_us_territory is False

        result = self.classifier.classify(50.0, -100.0)  # North of CONUS
        assert result.is_us_territory is False

    def test_classify_ocean_areas(self):
        """Test ocean area classification."""
        # Central Pacific Ocean
        result = self.classifier.classify(20.0, -150.0)
        assert result.is_land is False

        # Central Atlantic Ocean
        result = self.classifier.classify(20.0, -30.0)
        assert result.is_land is False

        # Continental landmass
        result = self.classifier.classify(40.0, -100.0)  # Kansas
        assert result.is_land is True

    def test_biosample_classification(self):
        """Test biosample-specific classification."""
        # US land location
        result = self.classifier.classify_biosample_location(40.0, -100.0)
        assert result["is_us_territory"] is True
        assert result["is_land"] is True
        assert "usgs" in result["recommended_providers"]
        assert result["routing_hint"] == "us_land"

        # Ocean location
        result = self.classifier.classify_biosample_location(20.0, -150.0)
        assert result["is_land"] is False
        assert result["routing_hint"] == "ocean"

        # International land
        result = self.classifier.classify_biosample_location(51.5074, -0.1278)  # London
        assert result["is_us_territory"] is False
        assert "open_topo_data" in result["recommended_providers"]
        assert result["routing_hint"] == "international_land"


class TestElevationProviders:
    """Test individual elevation providers with live API calls."""

    @pytest.mark.integration
    def test_usgs_provider_live(self):
        """Test USGS provider with live API call to known US location."""
        provider = USGSElevationProvider()

        # Test with Mount Rushmore, SD (known US location with good elevation data)
        result = provider.fetch(43.8791, -103.4591, timeout_s=30)

        assert result.ok is True
        assert result.elevation is not None
        assert result.elevation > 1000  # Mount Rushmore is at high elevation
        assert result.vertical_datum == "NAVD88"
        assert result.resolution_m <= 10.0  # Should be 10m or better
        assert result.location is not None
        assert abs(result.location.lat - 43.8791) < 0.01
        assert abs(result.location.lon - (-103.4591)) < 0.01

    @pytest.mark.integration
    def test_osm_provider_live(self):
        """Test OSM provider with live API call."""
        provider = OSMElevationProvider()

        # Test with San Francisco (well-known location)
        result = provider.fetch(37.7749, -122.4194, timeout_s=30)

        # OSM should work globally
        assert result.ok is True
        assert result.elevation is not None
        assert result.vertical_datum == "EGM96"
        assert result.resolution_m == 90.0
        assert result.location is not None

    @pytest.mark.integration
    def test_open_topo_data_provider_live(self):
        """Test Open Topo Data provider with live API call."""
        provider = OpenTopoDataProvider()

        # Test with Mount Rushmore (known elevation)
        result = provider.fetch(43.8791, -103.4591, timeout_s=30)

        assert result.ok is True
        assert result.elevation is not None
        assert result.elevation > 1000  # Mount Rushmore is high elevation
        assert result.vertical_datum == "EGM96"
        assert result.resolution_m == 30.0  # SRTM 30m default
        assert result.location is not None

    @pytest.mark.skipif(
        not os.getenv("GOOGLE_MAIN_API_KEY"), reason="Google API key not available"
    )
    @pytest.mark.integration
    def test_google_provider_live(self):
        """Test Google provider with live API call (requires API key)."""
        provider = GoogleElevationProvider()  # Uses env var

        # Test with San Francisco
        result = provider.fetch(37.7749, -122.4194, timeout_s=30)

        assert result.ok is True
        assert result.elevation is not None
        assert result.vertical_datum == "EGM96"
        assert result.location is not None

    @pytest.mark.integration
    def test_usgs_provider_ocean_location(self):
        """Test USGS provider with ocean location (should return no data)."""
        provider = USGSElevationProvider()

        # Test with Pacific Ocean location
        result = provider.fetch(30.0, -140.0, timeout_s=30)

        # USGS returns various errors for ocean locations
        assert result.ok is False
        # Could be JSON parsing error or "no data" message
        assert (
            "No elevation data available" in result.error
            or "Expecting value" in result.error
        )

    def test_provider_invalid_coordinates(self):
        """Test providers with invalid coordinates."""
        provider = USGSElevationProvider()

        with pytest.raises(ValueError, match="Invalid latitude"):
            provider.fetch(91.0, 0.0)  # Invalid latitude

        with pytest.raises(ValueError, match="Invalid longitude"):
            provider.fetch(0.0, 181.0)  # Invalid longitude


class TestElevationService:
    """Test the elevation service orchestrator with live API calls."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create service with available providers (Google conditional on API key)
        self.service = ElevationService(
            enable_google=bool(os.getenv("GOOGLE_MAIN_API_KEY")),
            enable_usgs=True,
            enable_osm=True,
            enable_open_topo_data=True,
        )

    def test_service_provider_selection_us(self):
        """Test provider selection for US coordinates."""
        # San Francisco (US territory)
        classification = self.service.classify_coordinates(37.7749, -122.4194)
        providers = self.service.select_providers(classification)

        assert classification.is_us_territory is True
        # Should prefer USGS for US territory
        assert providers[0].name == "usgs_epqs"

    def test_service_provider_selection_non_us(self):
        """Test provider selection for non-US coordinates."""
        # London (non-US)
        classification = self.service.classify_coordinates(51.5074, -0.1278)
        providers = self.service.select_providers(classification)

        assert classification.is_us_territory is False
        # Should have OSM available for non-US
        provider_names = [p.name for p in providers]
        assert "osm_elevation" in provider_names

    def test_service_preferred_providers(self):
        """Test preferred provider override."""
        classification = self.service.classify_coordinates(37.7749, -122.4194)
        providers = self.service.select_providers(classification, preferred=["osm"])

        # Should respect preferred provider
        assert providers[0].name == "osm_elevation"

    @pytest.mark.integration
    def test_service_get_elevation_us_location(self):
        """Test successful elevation lookup for US location."""
        request = ElevationRequest(
            latitude=43.8791, longitude=-103.4591
        )  # Mount Rushmore
        observations = self.service.get_elevation(request, timeout_s=30)

        assert len(observations) >= 1
        # At least one should succeed
        successful_obs = [
            obs for obs in observations if obs.value_status == ValueStatus.OK
        ]
        assert len(successful_obs) >= 1

        # Check USGS observation specifically
        usgs_obs = [obs for obs in observations if obs.provider.name == "usgs_epqs"]
        assert len(usgs_obs) == 1
        assert usgs_obs[0].value_numeric is not None
        assert usgs_obs[0].value_numeric > 1000  # Mount Rushmore elevation

    @pytest.mark.integration
    def test_service_get_elevation_non_us_location(self):
        """Test successful elevation lookup for non-US location."""
        request = ElevationRequest(latitude=51.5074, longitude=-0.1278)  # London
        observations = self.service.get_elevation(request, timeout_s=30)

        assert len(observations) >= 1
        # At least one should succeed
        successful_obs = [
            obs for obs in observations if obs.value_status == ValueStatus.OK
        ]
        assert len(successful_obs) >= 1

    def test_service_get_best_elevation(self):
        """Test best elevation selection logic."""
        from biosample_enricher.models import Observation, ProviderRef, Variable

        # Create test observations
        obs1 = Observation(
            variable=Variable.ELEVATION,
            value_numeric=100.0,
            value_status=ValueStatus.OK,
            provider=ProviderRef(name="provider1"),
            request_location=GeoPoint(lat=37.0, lon=-122.0),
            distance_to_input_m=0.0,
            spatial_resolution_m=10.0,
            normalization_version="test",
        )

        obs2 = Observation(
            variable=Variable.ELEVATION,
            value_numeric=102.0,
            value_status=ValueStatus.OK,
            provider=ProviderRef(name="provider2"),
            request_location=GeoPoint(lat=37.0, lon=-122.0),
            distance_to_input_m=5.0,
            spatial_resolution_m=30.0,
            normalization_version="test",
        )

        best = self.service.get_best_elevation([obs1, obs2])

        assert best is not None
        assert best.elevation_meters == 100.0  # Should prefer obs1 (closer distance)
        assert best.provider == "provider1"


class TestElevationUtils:
    """Test elevation utility functions."""

    def test_distance_calculation(self):
        """Test haversine distance calculation."""
        # Distance from SF to LA (approximately 559 km)
        sf_lat, sf_lon = 37.7749, -122.4194
        la_lat, la_lon = 34.0522, -118.2437

        distance = calculate_distance_m(sf_lat, sf_lon, la_lat, la_lon)

        # Should be approximately 559 km
        assert 550000 < distance < 570000

    def test_distance_same_point(self):
        """Test distance calculation for same point."""
        distance = calculate_distance_m(37.7749, -122.4194, 37.7749, -122.4194)
        assert distance == 0.0

    def test_distance_small_difference(self):
        """Test distance calculation for small differences."""
        # 0.001 degree difference (approximately 111 meters)
        distance = calculate_distance_m(37.7749, -122.4194, 37.7759, -122.4194)

        # Should be approximately 111 meters
        assert 100 < distance < 120


class TestElevationModels:
    """Test elevation data models."""

    def test_elevation_request_validation(self):
        """Test elevation request validation."""
        # Valid request
        request = ElevationRequest(latitude=37.7749, longitude=-122.4194)
        assert request.latitude == 37.7749
        assert request.longitude == -122.4194
        assert request.preferred_providers is None

    def test_coordinate_classification_model(self):
        """Test coordinate classification model."""
        classification = CoordinateClassification(
            is_us_territory=True, region="CONUS", confidence=0.95
        )

        assert classification.is_us_territory is True
        assert classification.region == "CONUS"
        assert classification.confidence == 0.95
        assert classification.is_land is None  # Default value

    def test_fetch_result_model(self):
        """Test fetch result model."""
        result = FetchResult(
            ok=True,
            elevation=100.0,
            location=GeoPoint(lat=37.0, lon=-122.0),
            raw={"test": "data"},
        )

        assert result.ok is True
        assert result.elevation == 100.0
        assert result.location.lat == 37.0
        assert result.error is None


class TestElevationEndToEnd:
    """End-to-end integration tests with full service."""

    @pytest.mark.integration
    def test_full_service_us_location(self):
        """Test complete elevation service with US location."""
        service = ElevationService.from_env()

        # Test Mount Rushmore
        request = ElevationRequest(latitude=43.8791, longitude=-103.4591)
        observations = service.get_elevation(request, timeout_s=30)

        # Should have at least USGS and OSM observations
        assert len(observations) >= 2

        # Get best elevation
        best = service.get_best_elevation(observations)
        assert best is not None
        assert best.elevation_meters > 1000

        # Create output envelope
        envelope = service.create_output_envelope("test-rushmore", observations)
        assert envelope.subject_id == "test-rushmore"
        assert len(envelope.observations) == len(observations)

    @pytest.mark.integration
    def test_full_service_international_location(self):
        """Test complete elevation service with international location."""
        service = ElevationService.from_env()

        # Test London, UK
        request = ElevationRequest(latitude=51.5074, longitude=-0.1278)
        observations = service.get_elevation(request, timeout_s=30)

        # Should have observations (at least OSM)
        assert len(observations) >= 1

        # Get best elevation
        best = service.get_best_elevation(observations)
        assert best is not None
        # London is relatively low elevation
        assert 0 <= best.elevation_meters <= 200

    @pytest.mark.integration
    def test_elevation_with_preferred_providers(self):
        """Test elevation lookup with preferred provider list."""
        service = ElevationService.from_env()

        # Test with OSM preference
        request = ElevationRequest(
            latitude=37.7749, longitude=-122.4194, preferred_providers=["osm"]
        )
        observations = service.get_elevation(request, timeout_s=30)

        assert len(observations) >= 1
        # First observation should be from OSM
        assert observations[0].provider.name == "osm_elevation"


if __name__ == "__main__":
    pytest.main([__file__])
