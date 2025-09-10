#!/usr/bin/env python3
"""
HTTP Cache Testing

Tests for MongoDB-based HTTP caching system following LinkML testing guidelines.
This module tests cache functionality using the Open Notify ISS Pass API.

Testing Standards (LinkML Guidelines):
1. Use pytest for all new tests
2. Group tests by scope/module under tests/ directory
3. Use small, purpose-built fixtures rather than large datasets
4. Apply pytest marks: @pytest.mark.network, @pytest.mark.slow
5. Use fixtures for reusable test components
6. Test both positive and negative cases
7. Mock external dependencies when appropriate

Test Categories:
- Unit tests: Core cache logic, canonicalization
- Integration tests: Full cache workflow with real API calls
- Network tests: External API interaction (marked as @pytest.mark.network)
- Slow tests: Tests with delays/timeouts (marked as @pytest.mark.slow)
"""

import json
import os
import time
from unittest.mock import Mock, patch

import pytest
import requests
from pymongo import MongoClient

from biosample_enricher.http_cache import (
    CachedHTTPClient,
    MongoHTTPCache,
    RequestCanonicalizer,
    get_cached_client,
    request,
)

# Test Configuration
SUNRISE_API_URL = "https://api.sunrise-sunset.org/json"
TEST_PARAMS = {
    "lat": 37.7749,
    "lng": -122.4194,
    "date": "2025-09-10",
}  # San Francisco coordinates
TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_DB_NAME = "test_http_cache"
TEST_COLLECTION_NAME = "test_requests"


# Fixtures
@pytest.fixture
def temp_mongo_uri():
    """Provide MongoDB URI for testing, defaulting to localhost."""
    return os.getenv("TEST_MONGO_URI", TEST_MONGO_URI)


@pytest.fixture
def cache_config():
    """Provide cache configuration for tests."""
    return {
        "database": TEST_DB_NAME,
        "collection": TEST_COLLECTION_NAME,
        "default_expire_after": 3600,  # 1 hour
        "coord_precision": 4,
        "truncate_dates": True,
    }


@pytest.fixture
def clean_cache_db(temp_mongo_uri, cache_config):
    """
    Ensure clean cache database for each test.

    This fixture:
    1. Drops the test database before each test
    2. Yields control to the test
    3. Cleans up after the test completes
    """
    try:
        client = MongoClient(temp_mongo_uri)
        # Clean up before test
        client.drop_database(cache_config["database"])
        yield
        # Clean up after test
        client.drop_database(cache_config["database"])
        client.close()
    except Exception:
        # If MongoDB is not available, skip cleanup
        yield


@pytest.fixture
def cache_instance(temp_mongo_uri, cache_config, clean_cache_db):
    """Create a MongoHTTPCache instance for testing."""
    try:
        cache = MongoHTTPCache(temp_mongo_uri, **cache_config)
        yield cache
        cache.close()
    except Exception as e:
        pytest.skip(f"MongoDB not available: {e}")


@pytest.fixture
def cached_client(cache_instance):
    """Create a CachedHTTPClient instance for testing."""
    client = CachedHTTPClient(cache=cache_instance)
    yield client
    client.close()


@pytest.fixture
def sample_response():
    """Mock response data for testing."""
    return {
        "message": "success",
        "request": {
            "altitude": 100,
            "datetime": 1519243200,
            "latitude": 37.7749,
            "longitude": -122.4194,
            "passes": 5,
        },
        "response": [
            {"duration": 649, "risetime": 1519243200},
            {"duration": 648, "risetime": 1519248900},
        ],
    }


# Unit Tests - Core Cache Logic
class TestRequestCanonicalizer:
    """Test the request canonicalization logic."""

    def test_coordinate_rounding(self):
        """Test latitude/longitude rounding to specified precision."""
        canonicalizer = RequestCanonicalizer(coord_precision=4)

        params = {"lat": 37.774929, "lon": -122.419416}
        result = canonicalizer.canonicalize_params(params)

        assert result["lat"] == 37.7749
        assert result["lon"] == -122.4194

    def test_coordinate_variations(self):
        """Test different coordinate field names."""
        canonicalizer = RequestCanonicalizer(coord_precision=2)

        test_cases = [
            ({"latitude": 37.774929}, {"latitude": 37.77}),
            ({"longitude": -122.419416}, {"longitude": -122.42}),
            ({"lng": -122.419416}, {"lng": -122.42}),
        ]

        for input_params, expected in test_cases:
            result = canonicalizer.canonicalize_params(input_params)
            assert result == expected

    def test_datetime_truncation(self):
        """Test datetime truncation to date format."""
        canonicalizer = RequestCanonicalizer(truncate_dates=True)

        test_cases = [
            ({"date": "2023-01-15T14:30:00Z"}, {"date": "2023-01-15"}),
            ({"datetime": "2023-01-15T14:30:00"}, {"datetime": "2023-01-15"}),
            ({"time": "2023-01-15T14:30:00.123456"}, {"time": "2023-01-15"}),
        ]

        for input_params, expected in test_cases:
            result = canonicalizer.canonicalize_params(input_params)
            assert result == expected

    def test_url_canonicalization(self):
        """Test URL path coordinate canonicalization."""
        canonicalizer = RequestCanonicalizer(coord_precision=2)

        # Test embedded coordinates in URL path
        test_url = "http://api.example.com/location/37.774929,-122.419416/data"
        result = canonicalizer.canonicalize_url(test_url)

        assert "37.77,-122.42" in result

    def test_no_changes_when_disabled(self):
        """Test that canonicalization can be disabled."""
        canonicalizer = RequestCanonicalizer(coord_precision=4, truncate_dates=False)

        params = {"datetime": "2023-01-15T14:30:00Z", "other": "value"}
        result = canonicalizer.canonicalize_params(params)

        assert result["datetime"] == "2023-01-15T14:30:00Z"
        assert result["other"] == "value"


class TestMongoHTTPCache:
    """Test MongoDB cache backend functionality."""

    def test_cache_initialization(self, temp_mongo_uri, cache_config):
        """Test cache initialization and connection."""
        try:
            cache = MongoHTTPCache(temp_mongo_uri, **cache_config)
            assert cache.mongo_uri == temp_mongo_uri
            assert cache.database_name == cache_config["database"]
            assert cache.collection_name == cache_config["collection"]
            cache.close()
        except Exception as e:
            pytest.skip(f"MongoDB not available: {e}")

    def test_cache_key_generation(self, cache_instance):
        """Test consistent cache key generation."""
        method = "GET"
        url = "http://api.example.com/test"
        params = {"lat": 37.7749, "lon": -122.4194}

        key1 = cache_instance._generate_cache_key(method, url, params)
        key2 = cache_instance._generate_cache_key(method, url, params)

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 64  # SHA256 hex digest length

    def test_cache_key_canonicalization(self, cache_instance):
        """Test that similar requests generate the same cache key."""
        method = "GET"
        url = "http://api.example.com/test"

        # These should generate the same key due to canonicalization
        params1 = {"lat": 37.774929, "lon": -122.419416}
        params2 = {"lat": 37.7749, "lon": -122.4194}  # Rounded values

        key1 = cache_instance._generate_cache_key(method, url, params1)
        key2 = cache_instance._generate_cache_key(method, url, params2)

        assert key1 == key2

    def test_cache_storage_and_retrieval(self, cache_instance, sample_response):
        """Test basic cache storage and retrieval."""
        if cache_instance._collection is None:
            pytest.skip("MongoDB not available for testing")

        # Create mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = json.dumps(sample_response).encode()
        mock_response.request = Mock()
        mock_response.request.headers = {"User-Agent": "test"}

        method = "GET"
        url = SUNRISE_API_URL
        params = TEST_PARAMS

        # Store in cache
        cache_instance.set(method, url, mock_response, params)

        # Retrieve from cache
        cached_entry = cache_instance.get(method, url, params)

        assert cached_entry is not None
        assert cached_entry.status_code == 200
        assert cached_entry.url == url
        assert cached_entry.method == method.upper()
        assert json.loads(cached_entry.response_body.decode()) == sample_response

    def test_cache_expiration(self, cache_instance, sample_response):
        """Test cache entry expiration."""
        if cache_instance._collection is None:
            pytest.skip("MongoDB not available for testing")

        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = json.dumps(sample_response).encode()
        mock_response.request = Mock()
        mock_response.request.headers = {}

        method = "GET"
        url = SUNRISE_API_URL
        params = TEST_PARAMS

        # Store with very short expiration (1 second)
        cache_instance.set(method, url, mock_response, params, expire_after=1)

        # Should be retrievable immediately
        cached_entry = cache_instance.get(method, url, params)
        assert cached_entry is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired and removed
        cached_entry = cache_instance.get(method, url, params)
        assert cached_entry is None

    def test_cache_stats(self, cache_instance, sample_response):
        """Test cache statistics generation."""
        if cache_instance._collection is None:
            # Test graceful degradation when MongoDB is not available
            stats = cache_instance.stats()
            assert "error" in stats
            return

        # Initially empty
        stats = cache_instance.stats()
        assert stats["total_entries"] == 0

        # Add a few entries
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = json.dumps(sample_response).encode()
        mock_response.request = Mock()
        mock_response.request.headers = {}

        for i in range(3):
            cache_instance.set("GET", f"http://test{i}.com", mock_response)

        stats = cache_instance.stats()
        assert stats["total_entries"] == 3
        assert stats["by_method"]["GET"] == 3
        assert stats["by_status_code"][200] == 3

    def test_cache_clear(self, cache_instance, sample_response):
        """Test cache clearing functionality."""
        if cache_instance._collection is None:
            # Test graceful degradation when MongoDB is not available
            deleted_count = cache_instance.clear()
            assert deleted_count == 0
            return

        # Add entries
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = json.dumps(sample_response).encode()
        mock_response.request = Mock()
        mock_response.request.headers = {}

        cache_instance.set("GET", "http://test1.com", mock_response)
        cache_instance.set("GET", "http://test2.com", mock_response)

        # Verify entries exist
        stats = cache_instance.stats()
        assert stats["total_entries"] == 2

        # Clear cache
        deleted_count = cache_instance.clear()
        assert deleted_count == 2

        # Verify cache is empty
        stats = cache_instance.stats()
        assert stats["total_entries"] == 0


# Integration Tests - Full Cache Workflow
class TestCachedHTTPClient:
    """Test the full cached HTTP client functionality."""

    def test_cache_miss_and_hit_cycle(self, cached_client):
        """Test complete cache miss -> store -> hit cycle with mocked response."""
        if cached_client.cache is None or cached_client.cache._collection is None:
            pytest.skip("MongoDB cache not available for testing")

        with patch.object(cached_client.session, "request") as mock_request:
            # Mock response
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.content = b'{"test": "data"}'
            mock_response.request = Mock()
            mock_response.request.headers = {}
            mock_request.return_value = mock_response

            url = "http://api.example.com/test"
            params = {"param": "value"}

            # First request - should miss cache and call API
            response1 = cached_client.get(url, params=params)
            assert not getattr(response1, "_from_cache", True)
            assert mock_request.call_count == 1

            # Second request - should hit cache
            response2 = cached_client.get(url, params=params)
            assert getattr(response2, "_from_cache", False)
            assert mock_request.call_count == 1  # No additional API call

            # Verify responses are equivalent
            assert response1.status_code == response2.status_code
            assert response1.content == response2.content

    def test_cache_control_parameters(self, cached_client):
        """Test read_from_cache and write_to_cache parameters."""
        if cached_client.cache is None or cached_client.cache._collection is None:
            pytest.skip("MongoDB cache not available for testing")

        with patch.object(cached_client.session, "request") as mock_request:
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b'{"test": "data"}'
            mock_response.request = Mock()
            mock_response.request.headers = {}
            mock_request.return_value = mock_response

            url = "http://api.example.com/test"

            # First request with caching enabled
            cached_client.get(url, read_from_cache=True, write_to_cache=True)
            assert mock_request.call_count == 1

            # Second request with read disabled (should bypass cache)
            response2 = cached_client.get(
                url, read_from_cache=False, write_to_cache=True
            )
            assert mock_request.call_count == 2
            assert not getattr(response2, "_from_cache", True)

            # Third request with read enabled (should hit cache from first request)
            response3 = cached_client.get(
                url, read_from_cache=True, write_to_cache=True
            )
            assert mock_request.call_count == 2  # No additional call
            assert getattr(response3, "_from_cache", False)

    def test_coordinate_canonicalization_in_practice(self, cached_client):
        """Test that coordinate canonicalization works in real requests."""
        if cached_client.cache is None or cached_client.cache._collection is None:
            pytest.skip("MongoDB cache not available for testing")

        with patch.object(cached_client.session, "request") as mock_request:
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b'{"location": "data"}'
            mock_response.request = Mock()
            mock_response.request.headers = {}
            mock_request.return_value = mock_response

            url = "http://api.example.com/location"

            # Request with high precision coordinates
            params1 = {"lat": 37.774929483, "lon": -122.419416284}
            cached_client.get(url, params=params1)
            assert mock_request.call_count == 1

            # Request with rounded coordinates (should hit cache)
            params2 = {"lat": 37.7749, "lon": -122.4194}
            response2 = cached_client.get(url, params=params2)
            assert (
                mock_request.call_count == 1
            )  # No additional call due to canonicalization
            assert getattr(response2, "_from_cache", False)

    def test_different_http_methods(self, cached_client):
        """Test caching with different HTTP methods."""
        if cached_client.cache is None or cached_client.cache._collection is None:
            pytest.skip("MongoDB cache not available for testing")

        with patch.object(cached_client.session, "request") as mock_request:
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b'{"method": "test"}'
            mock_response.request = Mock()
            mock_response.request.headers = {}
            mock_request.return_value = mock_response

            url = "http://api.example.com/test"

            # GET request
            cached_client.get(url)
            assert mock_request.call_count == 1

            # POST request to same URL (should be separate cache entry)
            cached_client.post(url, json={"data": "test"})
            assert mock_request.call_count == 2

            # Another GET request (should hit cache)
            response3 = cached_client.get(url)
            assert mock_request.call_count == 2
            assert getattr(response3, "_from_cache", False)

    def test_error_response_not_cached(self, cached_client):
        """Test that error responses (4xx, 5xx) are not cached."""
        with patch.object(cached_client.session, "request") as mock_request:
            # Mock error response
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 404
            mock_response.headers = {}
            mock_response.content = b'{"error": "Not found"}'
            mock_response.request = Mock()
            mock_response.request.headers = {}
            mock_request.return_value = mock_response

            url = "http://api.example.com/notfound"

            # First request (404 error)
            response1 = cached_client.get(url)
            assert response1.status_code == 404
            assert mock_request.call_count == 1

            # Second request (should not use cache, make new request)
            response2 = cached_client.get(url)
            assert mock_request.call_count == 2
            assert not getattr(response2, "_from_cache", True)


# Network Tests - Real API Interaction
class TestNetworkIntegration:
    """
    Network integration tests using real API calls.

    These tests are marked with @pytest.mark.network and are skipped in CI
    but can be run locally to test real network interaction.
    """

    @pytest.mark.network
    def test_sunrise_api_cache_integration(self, cached_client):
        """Test complete integration with Sunrise-Sunset API."""
        url = SUNRISE_API_URL
        params = TEST_PARAMS

        # First request - should hit the API
        start_time = time.time()
        response1 = cached_client.get(url, params=params, timeout=10)
        first_request_time = time.time() - start_time

        assert response1.status_code == 200
        assert not getattr(response1, "_from_cache", True)

        data1 = response1.json()
        assert data1["status"] == "OK"
        assert "results" in data1

        # Second request - should use cache (much faster)
        start_time = time.time()
        response2 = cached_client.get(url, params=params, timeout=10)
        second_request_time = time.time() - start_time

        assert response2.status_code == 200
        assert getattr(response2, "_from_cache", False)

        data2 = response2.json()
        assert data1 == data2  # Same data from cache

        # Cache should be significantly faster
        assert second_request_time < first_request_time / 2

    @pytest.mark.network
    def test_sunrise_api_coordinate_canonicalization(self, cached_client):
        """Test coordinate canonicalization with real Sunrise-Sunset API."""
        url = SUNRISE_API_URL

        # Request with high precision
        precise_params = {
            "lat": 37.774929483,
            "lng": -122.419416284,
            "date": "2025-09-10",
        }
        response1 = cached_client.get(url, params=precise_params, timeout=10)
        assert response1.status_code == 200
        assert not getattr(response1, "_from_cache", True)

        # Request with rounded coordinates (should hit cache)
        rounded_params = {"lat": 37.7749, "lng": -122.4194, "date": "2025-09-10"}
        response2 = cached_client.get(url, params=rounded_params, timeout=10)
        assert response2.status_code == 200
        assert getattr(response2, "_from_cache", False)

        # Responses should be identical
        assert response1.json() == response2.json()

    @pytest.mark.network
    def test_sunrise_api_different_locations(self, cached_client):
        """Test that different locations create separate cache entries."""
        url = SUNRISE_API_URL

        # San Francisco
        sf_params = {"lat": 37.7749, "lng": -122.4194, "date": "2025-09-10"}
        sf_response = cached_client.get(url, params=sf_params, timeout=10)
        assert sf_response.status_code == 200

        # New York (should be separate cache entry)
        ny_params = {"lat": 40.7128, "lng": -74.0060, "date": "2025-09-10"}
        ny_response = cached_client.get(url, params=ny_params, timeout=10)
        assert ny_response.status_code == 200
        assert not getattr(ny_response, "_from_cache", True)

        # San Francisco again (should hit cache)
        sf_response2 = cached_client.get(url, params=sf_params, timeout=10)
        assert getattr(sf_response2, "_from_cache", False)


# Slow Tests - Performance and Timing
class TestPerformanceAndTiming:
    """
    Performance tests that may take longer to run.

    These tests are marked with @pytest.mark.slow and may be skipped
    in rapid development cycles.
    """

    @pytest.mark.slow
    def test_cache_expiration_timing(self, cached_client):
        """Test cache expiration with real timing."""
        with patch.object(cached_client.session, "request") as mock_request:
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b'{"expiration": "test"}'
            mock_response.request = Mock()
            mock_response.request.headers = {}
            mock_request.return_value = mock_response

            url = "http://api.example.com/expire-test"

            # Request with 2-second expiration
            cached_client.get(url, expire_after=2)
            assert mock_request.call_count == 1

            # Immediate second request (should hit cache)
            response2 = cached_client.get(url)
            assert getattr(response2, "_from_cache", False)
            assert mock_request.call_count == 1

            # Wait for expiration
            time.sleep(2.5)

            # Request after expiration (should miss cache)
            response3 = cached_client.get(url)
            assert not getattr(response3, "_from_cache", True)
            assert mock_request.call_count == 2

    @pytest.mark.slow
    def test_high_volume_caching(self, cached_client):
        """Test cache performance with multiple requests."""
        with patch.object(cached_client.session, "request") as mock_request:
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b'{"volume": "test"}'
            mock_response.request = Mock()
            mock_response.request.headers = {}
            mock_request.return_value = mock_response

            base_url = "http://api.example.com/volume-test"

            # Make many unique requests (should all miss cache)
            for i in range(10):
                response = cached_client.get(f"{base_url}/{i}")
                assert response.status_code == 200

            assert mock_request.call_count == 10

            # Repeat same requests (should all hit cache)
            start_time = time.time()
            for i in range(10):
                response = cached_client.get(f"{base_url}/{i}")
                assert getattr(response, "_from_cache", False)
            cache_time = time.time() - start_time

            # Should still be only 10 API calls total
            assert mock_request.call_count == 10

            # Cache requests should be fast
            assert cache_time < 1.0  # All 10 cache hits should take less than 1 second


# Global Function Tests
class TestGlobalFunctions:
    """Test the global convenience functions."""

    def test_global_request_function(self):
        """Test the global request function."""
        with patch(
            "biosample_enricher.http_cache.get_cached_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_response = Mock(spec=requests.Response)
            mock_client.request.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Use global request function
            response = request("GET", "http://test.com", params={"test": "value"})

            assert response == mock_response
            mock_client.request.assert_called_once_with(
                "GET",
                "http://test.com",
                params={"test": "value"},
                json=None,
                read_from_cache=True,
                write_to_cache=True,
                expire_after=None,
            )

    def test_get_cached_client_singleton(self):
        """Test that get_cached_client returns a singleton."""
        # Clear any existing global client
        import biosample_enricher.http_cache

        biosample_enricher.http_cache._client = None

        with patch(
            "biosample_enricher.http_cache.CachedHTTPClient"
        ) as mock_client_class:
            mock_instance = Mock()
            mock_client_class.return_value = mock_instance

            # First call should create instance
            client1 = get_cached_client()
            assert client1 == mock_instance
            assert mock_client_class.call_count == 1

            # Second call should return same instance
            client2 = get_cached_client()
            assert client2 == mock_instance
            assert mock_client_class.call_count == 1  # No additional creation


# Error Handling Tests
class TestErrorHandling:
    """Test error handling in cache system."""

    def test_mongo_unavailable_graceful_degradation(self):
        """Test graceful degradation when MongoDB is unavailable."""
        # Try to create cache with invalid URI
        cache = MongoHTTPCache("mongodb://invalid:27017", database="test")

        # Cache operations should not raise exceptions, just return None/empty
        assert cache.get("GET", "http://test.com") is None

        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b"test"
        mock_response.request = Mock()
        mock_response.request.headers = {}

        # Set operation should not raise exception
        cache.set("GET", "http://test.com", mock_response)

        # Stats should return error message
        stats = cache.stats()
        assert "error" in stats

    def test_invalid_response_handling(self, cache_instance):
        """Test handling of invalid responses."""
        # Try to cache a response with missing required attributes
        invalid_response = Mock()
        # Missing status_code, headers, content, etc.

        # Should not raise exception
        try:
            cache_instance.set("GET", "http://test.com", invalid_response)
        except Exception as e:
            # Some error is expected, but it shouldn't crash the application
            assert isinstance(e, AttributeError | TypeError)

    def test_malformed_cache_entry_handling(self, cache_instance):
        """Test handling of malformed cache entries."""
        # This would test recovery from corrupted cache data
        # Implementation depends on specific error handling strategy
        pass


if __name__ == "__main__":
    pytest.main([__file__])
