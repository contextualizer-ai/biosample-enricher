#!/usr/bin/env python3
"""
HTTP Cache Testing

Simple integration tests for the HTTP caching system using requests-cache.
Tests demonstrate:
- Cache clearing
- First request hits API
- Subsequent request uses cache
- Cache cleanup

No mocking or patching - real integration tests against live APIs.
"""

import time

import pytest
import requests_cache

from biosample_enricher.http_cache import canonicalize_coords, get_session, request


class TestCoordinateCanonicalizer:
    """Test coordinate canonicalization logic."""

    def test_coordinate_rounding(self):
        """Test latitude/longitude rounding to 4 decimal places."""
        params = {"lat": 37.774929, "lng": -122.419416}
        result = canonicalize_coords(params)

        assert result["lat"] == 37.7749
        assert result["lng"] == -122.4194

    def test_coordinate_variations(self):
        """Test different coordinate field names."""
        test_cases = [
            ({"latitude": 37.774929}, {"latitude": 37.7749}),
            ({"longitude": -122.419416}, {"longitude": -122.4194}),
            ({"lon": -122.419416}, {"lon": -122.4194}),
        ]

        for input_params, expected in test_cases:
            result = canonicalize_coords(input_params)
            assert result == expected

    def test_datetime_truncation(self):
        """Test datetime truncation to date format."""
        test_cases = [
            ({"date": "2023-01-15T14:30:00Z"}, {"date": "2023-01-15"}),
            ({"datetime": "2023-01-15T14:30:00"}, {"datetime": "2023-01-15"}),
            ({"time": "2023-01-15T14:30:00.123456"}, {"time": "2023-01-15"}),
        ]

        for input_params, expected in test_cases:
            result = canonicalize_coords(input_params)
            assert result == expected


class TestCacheIntegration:
    """Integration tests demonstrating cache behavior with real APIs."""

    def test_cache_session_creation(self):
        """Test that we can create a cached session."""
        session = get_session()
        assert isinstance(session, requests_cache.CachedSession)
        assert session.cache is not None

    @pytest.mark.network
    def test_cache_lifecycle(self):
        """Test complete cache lifecycle: clear, request, cache hit, cleanup."""
        # Clear cache to start fresh
        session = get_session()
        session.cache.clear()

        # First request - should hit the API
        url = "https://api.sunrise-sunset.org/json"
        params = {"lat": 37.7749, "lng": -122.4194, "date": "2025-09-10"}

        start_time = time.time()
        response1 = request("GET", url, params=params, timeout=10)
        first_request_time = time.time() - start_time

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["status"] == "OK"

        # Check that this was NOT from cache
        assert not getattr(response1, "from_cache", False)

        # Second request - should use cache (much faster)
        start_time = time.time()
        response2 = request("GET", url, params=params, timeout=10)
        second_request_time = time.time() - start_time

        assert response2.status_code == 200
        data2 = response2.json()
        assert data1 == data2  # Same data from cache

        # Check that this WAS from cache
        assert getattr(response2, "from_cache", False)

        # Cache should be significantly faster
        assert second_request_time < first_request_time / 2

        # Cleanup - clear cache again
        session.cache.clear()

    @pytest.mark.network
    def test_coordinate_canonicalization_in_cache(self):
        """Test that coordinate canonicalization works for caching."""
        session = get_session()
        session.cache.clear()

        url = "https://api.sunrise-sunset.org/json"

        # Request with high precision coordinates
        precise_params = {
            "lat": 37.774929483,
            "lng": -122.419416284,
            "date": "2025-09-11",
        }
        response1 = request("GET", url, params=precise_params, timeout=10)
        assert response1.status_code == 200
        assert not getattr(response1, "from_cache", False)

        # Request with rounded coordinates (should hit cache due to canonicalization)
        rounded_params = {"lat": 37.7749, "lng": -122.4194, "date": "2025-09-11"}
        response2 = request("GET", url, params=rounded_params, timeout=10)
        assert response2.status_code == 200
        assert getattr(response2, "from_cache", False)

        # Both should return the same data
        assert response1.json() == response2.json()

        # Cleanup
        session.cache.clear()

    @pytest.mark.network
    def test_different_locations_separate_cache(self):
        """Test that different locations create separate cache entries."""
        session = get_session()
        session.cache.clear()

        url = "https://api.sunrise-sunset.org/json"

        # San Francisco
        sf_params = {"lat": 37.7749, "lng": -122.4194, "date": "2025-09-12"}
        sf_response = request("GET", url, params=sf_params, timeout=10)
        assert sf_response.status_code == 200
        assert not getattr(sf_response, "from_cache", False)

        # New York (different location - should be separate cache entry)
        ny_params = {"lat": 40.7128, "lng": -74.0060, "date": "2025-09-12"}
        ny_response = request("GET", url, params=ny_params, timeout=10)
        assert ny_response.status_code == 200
        assert not getattr(ny_response, "from_cache", False)

        # San Francisco again (should hit cache)
        sf_response2 = request("GET", url, params=sf_params, timeout=10)
        assert getattr(sf_response2, "from_cache", False)

        # Cleanup
        session.cache.clear()


if __name__ == "__main__":
    pytest.main([__file__])
