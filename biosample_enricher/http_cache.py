"""
Simple HTTP caching with coordinate canonicalization using requests-cache.
"""

import os
import uuid
from typing import Any

import requests
import requests_cache
from pymongo import MongoClient
from requests_cache import CachedSession, create_key

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)
DEBUG = os.getenv("DEBUG_HTTP_CACHE")


def canonicalize_coords(params: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize coordinate parameters for consistent caching."""
    if not params:
        return params

    canonical: dict[str, Any] = {}
    for key, value in params.items():
        key_lower = key.lower()

        # Round coordinates to 4 decimal places
        if key_lower in {"lat", "latitude", "lon", "lng", "longitude"}:
            try:
                canonical[key] = round(float(value), 4)
            except (ValueError, TypeError):
                canonical[key] = value
        # Truncate ISO datetimes to dates
        elif "date" in key_lower or "time" in key_lower:
            if isinstance(value, str) and "T" in value:
                canonical[key] = value.split("T")[0]
            else:
                canonical[key] = value
        else:
            canonical[key] = value

    return canonical


def _key_with_auth(request, ignored_parameters=None, match_headers=None, **kwargs):
    """Include all params (don't ignore 'key') and auth headers to keep auth in cache key."""
    return create_key(
        request=request,
        ignored_parameters=[],  # Don't ignore any parameters, especially 'key'
        match_headers=['X-Goog-Api-Key', 'Authorization'],
        **kwargs
    )


def _cache_ok(response):
    """Don't cache non-200 responses; also skip 200+error payloads from Google endpoints."""
    if response.status_code != 200:
        return False
    url = response.url or ""
    if 'googleapis.com' in url or 'maps.googleapis.com' in url:
        try:
            j = response.json()
            if ('error' in j and 'message' in j['error']) or 'error_message' in j:
                return False
        except Exception:
            pass
    return True


def get_session() -> CachedSession:
    """Get cached session with MongoDB (dev) or SQLite (CI) backend."""

    # Use SQLite in CI, MongoDB locally
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        logger.info("Using SQLite cache backend for CI environment")
        backend: requests_cache.SQLiteCache | requests_cache.MongoCache = (
            requests_cache.SQLiteCache("http_cache")
        )
    else:
        try:
            mongo_uri = os.getenv("CACHE_MONGO_CONNECTION", "mongodb://localhost:27017")
            # Remove database name from URI since it's specified separately to MongoCache
            base_uri = mongo_uri.split('/')[0] + '//' + mongo_uri.split('//')[1].split('/')[0]
            logger.debug(f"Attempting MongoDB connection to {base_uri}")
            client: MongoClient = MongoClient(base_uri, serverSelectionTimeoutMS=1000)
            client.admin.command("ping")  # Test connection
            backend = requests_cache.MongoCache(db_name="http_cache", connection=client)
            logger.info("Using MongoDB cache backend")
        except Exception as e:
            # Fall back to SQLite if MongoDB unavailable
            logger.warning(f"MongoDB unavailable, falling back to SQLite: {e}")
            backend = requests_cache.SQLiteCache("http_cache")

    from biosample_enricher.config import get_settings
    
    settings = get_settings()
    
    sess = CachedSession(
        backend=backend,
        cache_name=settings.cache.cache_name,
        key_fn=_key_with_auth,
        cache_control=True,      # Respect Cache-Control headers from APIs
        allowable_codes=(200,),  # Only cache 200 responses
        expire_after=settings.cache.ttl_seconds,
        filter_fn=_cache_ok,     # Additional filtering for Google error responses
    )
    
    if DEBUG:
        rid = os.getenv("RUN_ID") or uuid.uuid4().hex[:8]
        print(
            f"[HTTP-CACHE DEBUG {rid}] "
            f"backend={backend} name={settings.cache.cache_name} "
            f"allowable_codes={(200,)} filter_fn={_cache_ok.__name__} key_fn={_key_with_auth.__name__}"
        )
    
    return sess


def request(
    method: str,
    url: str,
    read_from_cache: bool = True,
    write_to_cache: bool = True,
    **kwargs: Any,
) -> requests.Response:
    """
    Make cached HTTP request with coordinate canonicalization.

    Args:
        method: HTTP method
        url: Request URL
        read_from_cache: Whether to read from cache
        write_to_cache: Whether to write to cache
        **kwargs: Additional request parameters

    Returns:
        HTTP response
    """
    # Canonicalize coordinates in params
    if "params" in kwargs:
        original_params = kwargs["params"].copy() if kwargs["params"] else {}
        kwargs["params"] = canonicalize_coords(kwargs["params"])
        if original_params != kwargs["params"]:
            logger.debug(
                f"Canonicalized coordinates: {original_params} -> {kwargs['params']}"
            )

    logger.debug(f"Making {method} request to {url}")

    # Handle cache control
    if not read_from_cache or not write_to_cache:
        # Create a temporary session with different cache settings
        if not read_from_cache and not write_to_cache:
            # No caching at all
            session = requests.Session()
        elif not read_from_cache:
            # Write to cache but don't read from it (force refresh)
            session = get_session()
            # Force cache bypass by adding a cache-busting parameter
            if "params" not in kwargs:
                kwargs["params"] = {}
            # We'll handle this by clearing cache for this specific request
            if hasattr(session.cache, "delete_url"):
                session.cache.delete_url(url, kwargs.get("params", {}))
        else:
            # Read from cache but don't write (read-only mode)
            session = get_session()
            # This is trickier - we'll need to use the session normally
            # but prevent writing by temporarily disabling cache
            original_disabled = getattr(session.cache, "disabled", False)
            if hasattr(session.cache, "disabled"):
                session.cache.disabled = True
    else:
        # Normal cached operation
        session = get_session()

    try:
        response = session.request(method, url, **kwargs)

        # Restore cache state if we modified it
        if (
            not write_to_cache
            and hasattr(session, "cache")
            and hasattr(session.cache, "disabled")
        ):
            session.cache.disabled = False

        cache_status = "HIT" if getattr(response, "from_cache", False) else "MISS"
        if not read_from_cache:
            cache_status = "BYPASS"
        logger.debug(
            f"{method} {url} -> {response.status_code} (Cache: {cache_status})"
        )

        return response
    finally:
        # Ensure cache state is restored
        if (
            hasattr(session, "cache")
            and hasattr(session.cache, "disabled")
            and "original_disabled" in locals()
        ):
            session.cache.disabled = original_disabled
