#!/usr/bin/env python3
"""
Sunrise-Sunset API Cache Integration Demo

This is a simple demonstration of how to use the HTTP cache with a real API.
Run this manually to test the cache functionality with the Sunrise-Sunset API.

Usage:
    uv run python tests/examples/test_sunrise_api_demo.py

    # Or with pytest:
    uv run pytest tests/examples/test_sunrise_api_demo.py -m network -s
"""

import logging
import time

import pytest

from biosample_enricher.http_cache import get_session, request

logger = logging.getLogger(__name__)


@pytest.mark.network
def test_sunrise_api_cache_demo():
    """
    Demonstrate HTTP cache functionality with the Sunrise-Sunset API.

    This test shows:
    1. Cache miss on first request (hits the API)
    2. Cache hit on second request (much faster)
    3. Coordinate canonicalization (different precision gives same result)
    """
    logger.info("Sunrise-Sunset API Cache Demo starting")

    # Clear cache to start fresh
    session = get_session()
    session.cache.clear()

    # San Francisco coordinates
    url = "https://api.sunrise-sunset.org/json"
    params = {"lat": 37.7749, "lng": -122.4194, "date": "2025-09-10"}

    logger.info("Testing URL: %s with params: %s", url, params)

    # First request - should miss cache
    logger.info("First request (cache miss expected)...")
    start_time = time.time()

    try:
        response1 = request("GET", url, params=params, timeout=10)
        first_request_time = time.time() - start_time

        logger.info(
            "First request: status=%d, time=%.3fs, from_cache=%s",
            response1.status_code,
            first_request_time,
            getattr(response1, "from_cache", False),
        )

        if response1.status_code == 200:
            data = response1.json()
            if "results" in data:
                logger.info(
                    "Response: status=%s, sunrise=%s, sunset=%s",
                    data["status"],
                    data["results"]["sunrise"],
                    data["results"]["sunset"],
                )

        # Second request - should hit cache
        logger.info("Second request (cache hit expected)...")
        start_time = time.time()

        response2 = request("GET", url, params=params, timeout=10)
        second_request_time = time.time() - start_time

        logger.info(
            "Second request: status=%d, time=%.3fs, from_cache=%s",
            response2.status_code,
            second_request_time,
            getattr(response2, "from_cache", False),
        )

        # Test coordinate canonicalization
        logger.info("Testing coordinate canonicalization...")
        precise_params = {
            "lat": 37.774929483,
            "lng": -122.419416284,
            "date": "2025-09-10",
        }
        logger.info("High precision params: %s", precise_params)

        start_time = time.time()
        response3 = request("GET", url, params=precise_params, timeout=10)
        third_request_time = time.time() - start_time

        logger.info(
            "Third request: status=%d, time=%.3fs, from_cache=%s",
            response3.status_code,
            third_request_time,
            getattr(response3, "from_cache", False),
        )

        # Performance comparison
        speedup = (
            first_request_time / second_request_time
            if second_request_time < first_request_time
            else 0
        )
        logger.info(
            "Performance Summary: first=%.3fs, second=%.3fs, third=%.3fs, speedup=%.1fx",
            first_request_time,
            second_request_time,
            third_request_time,
            speedup,
        )

        # Validate responses are identical
        if (
            response1.status_code
            == response2.status_code
            == response3.status_code
            == 200
        ):
            data1 = response1.json()
            data2 = response2.json()
            data3 = response3.json()

            if data1 == data2 == data3:
                logger.info("All responses identical - cache working correctly")
            else:
                logger.warning("Response data differs between requests")

        logger.info("Demo completed successfully")

        # For pytest assertions
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert getattr(response2, "from_cache", False), (
            "Second request should hit cache"
        )
        assert getattr(response3, "from_cache", False), (
            "Third request should hit cache (canonicalization)"
        )

    except Exception as e:
        logger.error("Error during demo: %s", e)
        raise

    finally:
        # Clean up cache
        session.cache.clear()


if __name__ == "__main__":
    # Run the demo directly
    test_sunrise_api_cache_demo()
