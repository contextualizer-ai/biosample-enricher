"""Integration tests for Google APIs (Elevation and Geocoding)."""

import os

import pytest

from biosample_enricher.elevation.providers.google import GoogleElevationProvider
from biosample_enricher.reverse_geocoding.providers.google import (
    GoogleReverseGeocodingProvider,
)


@pytest.mark.integration
class TestGoogleAPIsIntegration:
    """Integration tests for Google APIs that require actual API calls."""

    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        key = os.getenv("GOOGLE_MAIN_API_KEY")
        if not key:
            pytest.skip("GOOGLE_MAIN_API_KEY not set")
        return key

    def test_google_elevation_api(self, api_key):
        """Test Google Elevation API with real API call."""
        provider = GoogleElevationProvider(api_key=api_key)

        # Test with known location (Mount Everest base camp)
        lat, lon = 28.0026, 86.8528
        result = provider.fetch(lat, lon, read_from_cache=False, write_to_cache=False)

        assert result.ok is True
        assert result.elevation is not None
        assert 5000 < result.elevation < 6000  # Expected range for base camp
        assert result.location is not None
        assert result.vertical_datum == "EGM96"

        print("\nGoogle Elevation API Test:")
        print(f"  Location: {lat:.4f}, {lon:.4f}")
        print(f"  Elevation: {result.elevation:.2f}m")
        print(f"  Resolution: {result.resolution_m}m")
        print(f"  Vertical Datum: {result.vertical_datum}")

    def test_google_reverse_geocoding_api(self, api_key):
        """Test Google Reverse Geocoding API with real API call."""
        provider = GoogleReverseGeocodingProvider(api_key=api_key)

        # Test with known location (Googleplex)
        lat, lon = 37.4224, -122.0856
        result = provider.fetch(
            lat, lon, read_from_cache=False, write_to_cache=False, limit=5
        )

        assert result.ok is True
        assert result.result is not None
        assert len(result.result.locations) > 0

        best_match = result.result.get_best_match()
        assert best_match is not None
        assert best_match.country == "United States"
        assert best_match.state == "California"
        assert (
            "Mountain View" in best_match.formatted_address
            or best_match.city == "Mountain View"
        )

        print("\nGoogle Reverse Geocoding API Test:")
        print(f"  Location: {lat:.4f}, {lon:.4f}")
        print(f"  Formatted Address: {best_match.formatted_address}")
        print(f"  Country: {best_match.country} ({best_match.country_code})")
        print(f"  State: {best_match.state}")
        print(f"  City: {best_match.city}")
        print(f"  Postcode: {best_match.postcode}")
        print(f"  Place ID: {best_match.place_id}")
        print(f"  Total Results: {len(result.result.locations)}")

    def test_google_apis_combined(self, api_key):
        """Test both Google APIs together for the same location."""
        elevation_provider = GoogleElevationProvider(api_key=api_key)
        geocoding_provider = GoogleReverseGeocodingProvider(api_key=api_key)

        # Test with a mountainous location (Yosemite Valley)
        lat, lon = 37.7456, -119.5936

        # Run both API calls
        elevation_result = elevation_provider.fetch(
            lat, lon, read_from_cache=False, write_to_cache=False
        )
        geocoding_result = geocoding_provider.fetch(
            lat, lon, read_from_cache=False, write_to_cache=False, limit=3
        )

        # Verify elevation result
        assert elevation_result.ok is True
        assert elevation_result.elevation is not None
        assert (
            1000 < elevation_result.elevation < 2500
        )  # Expected range for Yosemite Valley

        # Verify geocoding result
        assert geocoding_result.ok is True
        assert geocoding_result.result is not None
        best_match = geocoding_result.result.get_best_match()
        assert best_match is not None
        assert best_match.country == "United States"
        assert best_match.state == "California"

        print("\nCombined Google APIs Test (Yosemite Valley):")
        print(f"  Location: {lat:.4f}, {lon:.4f}")
        print(f"  Elevation: {elevation_result.elevation:.2f}m")
        print(f"  Address: {best_match.formatted_address}")
        print("  Place Components:")
        print(f"    - Country: {best_match.country}")
        print(f"    - State: {best_match.state}")
        print(f"    - County: {best_match.county}")
        print(f"    - City: {best_match.city}")

    def test_google_apis_ocean_location(self, api_key):
        """Test Google APIs with an ocean location."""
        elevation_provider = GoogleElevationProvider(api_key=api_key)
        geocoding_provider = GoogleReverseGeocodingProvider(api_key=api_key)

        # Test with Pacific Ocean location
        lat, lon = 30.0, -140.0

        # Test elevation (should be negative for ocean)
        elevation_result = elevation_provider.fetch(
            lat, lon, read_from_cache=False, write_to_cache=False
        )

        assert elevation_result.ok is True
        assert elevation_result.elevation is not None
        assert elevation_result.elevation < 0  # Below sea level

        # Test reverse geocoding (might return no results or ocean name)
        geocoding_result = geocoding_provider.fetch(
            lat, lon, read_from_cache=False, write_to_cache=False
        )

        assert geocoding_result.ok is True
        assert geocoding_result.result is not None
        # Ocean locations might have zero results

        print("\nOcean Location Test (Pacific Ocean):")
        print(f"  Location: {lat:.4f}, {lon:.4f}")
        print(f"  Elevation: {elevation_result.elevation:.2f}m (below sea level)")
        print(f"  Geocoding Results: {len(geocoding_result.result.locations)}")
        if geocoding_result.result.locations:
            best_match = geocoding_result.result.get_best_match()
            print(f"  Nearest: {best_match.formatted_address}")

    def test_google_apis_error_handling(self, api_key):
        """Test error handling for invalid coordinates."""
        elevation_provider = GoogleElevationProvider(api_key=api_key)
        geocoding_provider = GoogleReverseGeocodingProvider(api_key=api_key)

        # Test with invalid coordinates
        with pytest.raises(ValueError, match="Invalid latitude"):
            elevation_provider.fetch(91, 0)

        with pytest.raises(ValueError, match="Invalid longitude"):
            geocoding_provider.fetch(0, 181)

        print("\nError handling tests passed successfully")
