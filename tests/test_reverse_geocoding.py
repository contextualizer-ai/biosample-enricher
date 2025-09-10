"""Tests for reverse geocoding providers and service."""

import os
import time

import pytest

from biosample_enricher.reverse_geocoding import (
    GoogleReverseGeocodingProvider,
    OSMReverseGeocodingProvider,
    ReverseGeocodingService,
)
from biosample_enricher.reverse_geocoding_models import (
    AddressComponentType,
)


class TestOSMReverseGeocodingProvider:
    """Tests for OSM Nominatim reverse geocoding provider."""

    @pytest.fixture
    def provider(self):
        """Create OSM provider instance."""
        return OSMReverseGeocodingProvider()

    @pytest.mark.integration
    def test_fetch_success(self, provider):
        """Test successful reverse geocoding fetch with real API."""
        # Perform fetch with real API call to Googleplex location
        result = provider.fetch(37.4224, -122.0856)

        # Verify result
        assert result.ok is True
        assert result.result is not None
        assert len(result.result.locations) >= 1

        location = result.result.locations[0]
        assert location.formatted_address is not None
        assert (
            "Mountain View" in location.formatted_address
            or location.city == "Mountain View"
        )
        assert location.country == "United States"
        assert location.country_code == "US"
        assert location.state == "California"
        # Don't check exact values as they can change
        assert location.postcode is not None
        assert location.road is not None

    @pytest.mark.integration
    def test_fetch_with_multiple_results(self, provider):
        """Test fetching multiple results with real API."""
        # Test with a well-known location
        result = provider.fetch(37.4224, -122.0856, limit=3)

        assert result.ok is True
        assert result.result is not None
        # Should get at least one result
        assert len(result.result.locations) >= 1
        # All results should be near the requested location
        for location in result.result.locations:
            assert location.formatted_address is not None

    def test_fetch_invalid_coordinates(self, provider):
        """Test handling of invalid coordinates."""
        # Test with invalid latitude
        with pytest.raises(ValueError, match="Invalid latitude"):
            provider.fetch(91.0, 0.0)

        # Test with invalid longitude
        with pytest.raises(ValueError, match="Invalid longitude"):
            provider.fetch(0.0, 181.0)

    @pytest.mark.integration
    def test_rate_limiting(self, provider):
        """Test rate limiting for public Nominatim."""
        # First request
        start_time = time.time()
        result1 = provider.fetch(0, 0, read_from_cache=False)

        # Second request should be rate limited (1 second minimum)
        result2 = provider.fetch(1, 1, read_from_cache=False)
        elapsed = time.time() - start_time

        # Should take at least 1 second due to rate limiting
        assert elapsed >= 1.0
        # Both results should be valid (ocean locations)
        assert result1.ok is True
        assert result2.ok is True


class TestGoogleReverseGeocodingProvider:
    """Tests for Google Geocoding reverse geocoding provider."""

    @pytest.fixture
    def provider(self):
        """Create Google provider instance."""
        # Skip if no API key
        if not os.getenv("GOOGLE_MAIN_API_KEY"):
            pytest.skip("Google API key not available")
        return GoogleReverseGeocodingProvider()

    @pytest.mark.integration
    def test_fetch_success(self, provider):
        """Test successful reverse geocoding fetch with real API."""
        # Perform fetch with real API call to Googleplex location
        result = provider.fetch(37.4224, -122.0856)

        # Verify result
        assert result.ok is True
        assert result.result is not None
        assert len(result.result.locations) >= 1

        location = result.result.locations[0]
        assert location.formatted_address is not None
        assert location.country == "United States"
        assert location.country_code == "US"
        assert location.state == "California"
        assert location.state_code == "CA"
        assert (
            "Mountain View" in location.formatted_address
            or location.city == "Mountain View"
        )
        # Don't check exact values as they can change
        assert location.place_id is not None

    @pytest.mark.integration
    def test_fetch_ocean_location(self, provider):
        """Test fetching ocean location (may return zero results)."""
        # Test with middle of Pacific Ocean
        result = provider.fetch(0, -140)

        assert result.ok is True
        assert result.result is not None
        # Ocean locations may have zero results or generic ocean results
        if len(result.result.locations) == 0:
            assert result.result.status == "ZERO_RESULTS"

    def test_invalid_coordinates(self, provider):
        """Test validation of invalid coordinates."""
        # Test with invalid latitude
        with pytest.raises(ValueError, match="Invalid latitude"):
            provider.fetch(91.0, 0.0)

        # Test with invalid longitude
        with pytest.raises(ValueError, match="Invalid longitude"):
            provider.fetch(0.0, 181.0)

    @pytest.mark.integration
    def test_parse_address_components(self, provider):
        """Test parsing of address components with real API."""
        result = provider.fetch(37.4224, -122.0856)

        assert result.ok is True
        assert result.result is not None
        assert len(result.result.locations) >= 1

        location = result.result.locations[0]
        components = location.components

        # Check that we have some components
        assert len(components) > 0
        component_types = {c.type for c in components}
        # At minimum we should have country
        assert AddressComponentType.COUNTRY in component_types


class TestReverseGeocodingService:
    """Tests for reverse geocoding service."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return ReverseGeocodingService()

    @pytest.mark.integration
    def test_reverse_geocode_with_specific_provider(self, service):
        """Test reverse geocoding with specific provider."""
        # Use OSM provider which is always available
        result = service.reverse_geocode(37.4224, -122.0856, provider="osm")

        assert result is not None
        assert result.get_formatted_address() is not None
        assert len(result.locations) >= 1

    @pytest.mark.integration
    def test_reverse_geocode_auto_selection(self, service):
        """Test auto-selection of provider."""
        result = service.reverse_geocode(37.4224, -122.0856)

        assert result is not None
        assert result.get_formatted_address() is not None
        # Should use Google if available, otherwise OSM
        assert result.provider.name in ["google_geocoding", "osm_nominatim"]

    @pytest.mark.integration
    def test_reverse_geocode_multiple(self, service):
        """Test reverse geocoding with multiple providers."""
        results = service.reverse_geocode_multiple(37.4224, -122.0856)

        assert "osm" in results
        assert results["osm"].get_formatted_address() is not None

        if "google" in service.providers:
            assert "google" in results
            assert results["google"].get_formatted_address() is not None

    @pytest.mark.integration
    def test_compare_providers(self, service):
        """Test provider comparison functionality."""
        comparison = service.compare_providers(37.4224, -122.0856)

        assert "query" in comparison
        assert comparison["query"]["lat"] == 37.4224
        assert comparison["query"]["lon"] == -122.0856

        assert "providers" in comparison
        assert "osm" in comparison["providers"]

        # If both providers return US results, check consensus
        if (
            "osm" in comparison["providers"]
            and comparison["providers"]["osm"].get("country") == "United States"
            and "google" in comparison["providers"]
            and comparison["providers"]["google"].get("country") == "United States"
        ):
            assert "consensus" in comparison
            if "country" in comparison["consensus"]:
                assert comparison["consensus"]["country"]["value"] == "United States"

    def test_get_available_providers(self, service):
        """Test getting list of available providers."""
        providers = service.get_available_providers()
        assert "osm" in providers
        # Google may or may not be available depending on API key

    def test_get_provider(self, service):
        """Test getting specific provider."""
        osm_provider = service.get_provider("osm")
        assert osm_provider is not None
        assert osm_provider.name == "osm_nominatim"

        invalid_provider = service.get_provider("invalid")
        assert invalid_provider is None
