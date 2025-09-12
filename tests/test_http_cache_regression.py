#!/usr/bin/env python3
"""
Regression tests for HTTP cache auth-aware behavior.

Prevents cache poisoning where invalid API key responses get cached
and reused for valid API keys.

Uses isolated in-memory cache to avoid polluting shared state.
"""

import os

import pytest
import requests_cache
from requests_cache import create_key


# Build an isolated in-memory session for this test file
def _key_with_auth(request, ignored_parameters=None, match_headers=None, **kwargs):
    """Include all params (don't ignore 'key') and auth headers to keep auth in cache key."""
    return create_key(
        request=request,
        ignored_parameters=[],  # Don't ignore any parameters, especially 'key'
        match_headers=["X-Goog-Api-Key", "Authorization"],
        **kwargs,
    )


def _cache_ok(response):
    """Don't cache non-200 responses; also skip 200+error payloads from Google endpoints."""
    if response.status_code != 200:
        return False
    url = response.url or ""
    if "googleapis.com" in url or "maps.googleapis.com" in url:
        try:
            j = response.json()
            if ("error" in j and "message" in j["error"]) or "error_message" in j:
                return False
        except Exception:
            pass
    return True


@pytest.fixture(scope="module")
def isolated_session():
    """Memory backend ensures nothing is persisted to your shared cache."""
    s = requests_cache.CachedSession(
        backend="memory",
        key_fn=_key_with_auth,
        cache_control=True,
        allowable_codes=(200,),
        filter_fn=_cache_ok,
    )
    yield s


class TestHttpCacheRegression:
    """Regression tests for cache poisoning prevention."""

    def test_google_auth_errors_not_cached(self, isolated_session):
        """Test that Google API auth errors don't poison cache for valid keys."""
        # 1) Deliberately bad key -> expect 4xx OR 200-with-error JSON, and no caching
        bad = isolated_session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": "BAD"},
        )
        assert getattr(bad, "from_cache", False) is False

        # 2) Now use the real key; MUST NOT be served from cache created by (1)
        real_key = os.environ["GOOGLE_MAIN_API_KEY"]
        good = isolated_session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": real_key},
        )
        assert getattr(good, "from_cache", False) is False, (
            "Auth poisoning: a bad-key response was reused for a good key."
        )

    def test_error_responses_not_cached(self, isolated_session):
        """Test that 4xx/5xx responses are not cached."""
        # Make two identical bad-key calls; second should NOT come from cache
        r1 = isolated_session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": "BAD"},
        )
        r2 = isolated_session.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": "0,0", "key": "BAD"},
        )
        assert getattr(r1, "from_cache", False) is False
        assert getattr(r2, "from_cache", False) is False, (
            "4xx/Google-error payloads should not be cached"
        )
