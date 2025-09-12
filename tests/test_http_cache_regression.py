#!/usr/bin/env python3
"""
Regression tests for HTTP cache auth-aware behavior.

Prevents cache poisoning where invalid API key responses get cached
and reused for valid API keys.
"""

import os

import pytest

from biosample_enricher.http_cache import get_session


class TestHttpCacheRegression:
    """Regression tests for cache poisoning prevention."""

    def test_google_auth_errors_not_cached(self):
        """Test that Google API auth errors don't poison cache for valid keys."""
        session = get_session()
        
        # 1) Make a call guaranteed to auth-fail (bad key)
        bad_response = session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": "BAD_KEY"}
        )
        
        # Should not come from cache (first request)
        assert getattr(bad_response, "from_cache", False) is False
        # Should get auth error or quota exceeded
        assert bad_response.status_code in (200, 401, 403)
        
        # 2) Now call with real key; must not hit cache from step 1
        api_key = os.getenv("GOOGLE_MAIN_API_KEY")
        if not api_key:
            pytest.skip("Google API key not available")
            
        good_response = session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": api_key}
        )
        
        # Critical: If bad request got 401/403, good request must NOT come from cache
        # This would indicate cache poisoning
        if bad_response.status_code in (401, 403):
            assert not getattr(good_response, "from_cache", False), (
                "Invalid-response poisoning detected: auth error response was "
                "cached and reused for valid API key. This indicates missing "
                "auth-aware cache keys or 4xx response filtering."
            )
        
        # Good response should succeed
        assert good_response.status_code == 200

    def test_cache_keys_include_auth_params(self):
        """Test that different API keys create different cache entries."""
        session = get_session()
        
        # Two different keys should create separate cache entries
        response1 = session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": "key1"}
        )
        
        response2 = session.get(
            "https://maps.googleapis.com/maps/api/elevation/json", 
            params={"locations": "0,0", "key": "key2"}
        )
        
        # Both should be fresh requests (not from cache)
        # since they have different auth parameters
        assert getattr(response1, "from_cache", False) is False
        assert getattr(response2, "from_cache", False) is False
        
        # Repeat first request - should come from cache now
        response1_cached = session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": "key1"}  
        )
        
        # This should come from cache since it's identical to response1
        assert getattr(response1_cached, "from_cache", False) is True

    def test_error_responses_not_cached(self):
        """Test that 4xx/5xx responses are not cached."""
        session = get_session()
        
        # Make request that will likely return 4xx (bad key)
        response1 = session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": "INVALID"}
        )
        
        # Make same request again
        response2 = session.get(
            "https://maps.googleapis.com/maps/api/elevation/json", 
            params={"locations": "0,0", "key": "INVALID"}
        )
        
        # If first response was an error, second should not come from cache
        if response1.status_code >= 400:
            assert getattr(response2, "from_cache", False) is False, (
                f"Error response {response1.status_code} was cached, but should "
                "not be cached to prevent error response pollution."
            )