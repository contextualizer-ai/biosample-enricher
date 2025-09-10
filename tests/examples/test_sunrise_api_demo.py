#!/usr/bin/env python3
"""
Sunrise-Sunset API Cache Integration Demo

This is a simple demonstration of how to use the HTTP cache with a real API.
Run this manually to test the cache functionality with the Sunrise-Sunset API.

Usage:
    uv run python tests/examples/test_iss_api_demo.py

    # Or with pytest:
    uv run pytest tests/examples/test_iss_api_demo.py -m network -s
"""

import time

import pytest

from biosample_enricher.http_cache import CachedHTTPClient


@pytest.mark.network
def test_sunrise_api_cache_demo():
    """
    Demonstrate HTTP cache functionality with the Sunrise-Sunset API.

    This test shows:
    1. Cache miss on first request (hits the API)
    2. Cache hit on second request (much faster)
    3. Coordinate canonicalization (different precision gives same result)
    """
    print("\n🌅 Sunrise-Sunset API Cache Demo")
    print("=" * 50)

    # Create cached client with MongoDB configuration
    import os

    from pymongo import MongoClient

    mongo_uri = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017")
    database = "test_http_cache_demo"
    collection = "demo_requests"

    # Clean the demo database before starting
    try:
        mongo_client = MongoClient(mongo_uri)
        mongo_client.drop_database(database)
        mongo_client.close()
    except Exception:
        pass

    client = CachedHTTPClient(
        mongo_uri=mongo_uri,
        database=database,
        collection=collection,
        default_expire_after=3600,
        coord_precision=4,
        truncate_dates=True,
    )

    if client.cache is None:
        pytest.skip("MongoDB not available for cache demo")

    # San Francisco coordinates
    url = "https://api.sunrise-sunset.org/json"
    params = {"lat": 37.7749, "lng": -122.4194, "date": "2025-09-10"}

    print(f"Testing URL: {url}")
    print(f"Parameters: {params}")
    print()

    # First request - should miss cache
    print("📡 First request (cache miss expected)...")
    start_time = time.time()

    try:
        response1 = client.get(url, params=params, timeout=10)
        first_request_time = time.time() - start_time

        print(f"✅ Status: {response1.status_code}")
        print(f"⏱️  Time: {first_request_time:.3f} seconds")
        print(f"💾 From cache: {getattr(response1, '_from_cache', False)}")

        if response1.status_code == 200:
            data = response1.json()
            print(f"📊 Response: {data['status']}")
            if "results" in data:
                print(f"🌅 Sunrise: {data['results']['sunrise']}")
                print(f"🌇 Sunset: {data['results']['sunset']}")
        print()

        # Second request - should hit cache
        print("📡 Second request (cache hit expected)...")
        start_time = time.time()

        response2 = client.get(url, params=params, timeout=10)
        second_request_time = time.time() - start_time

        print(f"✅ Status: {response2.status_code}")
        print(f"⏱️  Time: {second_request_time:.3f} seconds")
        print(f"💾 From cache: {getattr(response2, '_from_cache', False)}")
        print()

        # Test coordinate canonicalization
        print("🎯 Testing coordinate canonicalization...")
        precise_params = {
            "lat": 37.774929483,
            "lng": -122.419416284,
            "date": "2025-09-10",
        }
        print(f"High precision params: {precise_params}")

        start_time = time.time()
        response3 = client.get(url, params=precise_params, timeout=10)
        third_request_time = time.time() - start_time

        print(f"✅ Status: {response3.status_code}")
        print(f"⏱️  Time: {third_request_time:.3f} seconds")
        print(f"💾 From cache: {getattr(response3, '_from_cache', False)}")
        print()

        # Performance comparison
        print("📈 Performance Summary:")
        print(f"   First request (API call): {first_request_time:.3f}s")
        print(f"   Second request (cache):   {second_request_time:.3f}s")
        print(f"   Third request (canon):    {third_request_time:.3f}s")

        if second_request_time < first_request_time:
            speedup = first_request_time / second_request_time
            print(f"   🚀 Cache speedup: {speedup:.1f}x faster")

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
                print("   ✅ All responses identical - cache working correctly!")
            else:
                print("   ⚠️  Response data differs between requests")

        print()
        print("🎉 Demo completed successfully!")

        # For pytest assertions
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert getattr(response2, "_from_cache", False), (
            "Second request should hit cache"
        )
        assert getattr(response3, "_from_cache", False), (
            "Third request should hit cache (canonicalization)"
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        raise

    finally:
        client.close()
        # Clean up demo database
        try:
            mongo_client = MongoClient(mongo_uri)
            mongo_client.drop_database(database)
            mongo_client.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Run the demo directly
    test_sunrise_api_cache_demo()
