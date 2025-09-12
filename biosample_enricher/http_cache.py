"""
Simple HTTP caching with coordinate canonicalization using requests-cache.
"""

import os
from typing import Any

import requests
from pymongo import MongoClient
from requests_cache import CachedSession, create_key

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)

# Module-level singleton (tests can override/reset)
_SESSION = None


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


def _key_with_auth(request, **kwargs):
    return create_key(
        request=request,
        ignored_parameters=[],  # don't ignore ?key=
        match_headers=["X-Goog-Api-Key", "Authorization"],
        **kwargs,
    )


def _cache_ok(response):
    if response.status_code != 200:
        return False
    url = getattr(response, "url", "") or ""
    if "googleapis.com" in url or "maps.googleapis.com" in url:
        try:
            j = response.json()
            if ("error" in j and "message" in j["error"]) or "error_message" in j:
                return False
        except Exception:
            pass
    return True


def _sqlite_session(cache_name: str) -> CachedSession:
    """Create SQLite-backed cached session."""
    logger.info(f"Using SQLite cache backend: {cache_name}")
    return CachedSession(
        cache_name=cache_name,
        backend="sqlite",
        key_fn=_key_with_auth,
        cache_control=True,
        allowable_codes=(200,),
        expire_after=3600,
        filter_fn=_cache_ok,
    )


def _mongo_session(
    uri: str, db_name: str, collection_name: str, timeout_ms: int = 5000
) -> CachedSession:
    """Create MongoDB-backed cached session."""
    logger.debug(f"Attempting MongoDB connection to {uri}")
    client: MongoClient = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
    client.admin.command("ping")  # Fail fast if unreachable
    logger.info(f"Using MongoDB cache backend: {db_name}.{collection_name}")
    return CachedSession(
        cache_name=collection_name,
        backend="mongodb",
        connection=client,
        key_fn=_key_with_auth,
        cache_control=True,
        allowable_codes=(200,),
        expire_after=3600,
        filter_fn=_cache_ok,
    )


def _make_session() -> CachedSession:
    """Create a new cached session with current settings."""
    # Defaults are CI- and prod-friendly (SQLite)
    backend = os.getenv("CACHE_BACKEND", "sqlite").lower()
    cache_name = os.getenv("CACHE_NAME", "cache/http")

    # Support pytest-xdist parallel testing with per-worker cache files
    xdist_worker = os.getenv("PYTEST_XDIST_WORKER")
    if xdist_worker and backend == "sqlite":
        cache_name = f"{cache_name}_{xdist_worker}"

    if backend == "mongodb":
        try:
            uri = os.environ["MONGO_URI"]  # Required for MongoDB
            db_name = os.getenv("MONGO_DB", "requests_cache")
            collection_name = os.getenv("MONGO_COLL", "http")
            return _mongo_session(uri, db_name, collection_name)
        except KeyError:
            logger.warning(
                "MongoDB backend requested but MONGO_URI not set, falling back to SQLite"
            )
            return _sqlite_session(cache_name)
        except Exception as e:
            # Graceful fallback keeps tests/CI green
            logger.warning(f"MongoDB connection failed, falling back to SQLite: {e}")
            return _sqlite_session(cache_name)

    return _sqlite_session(cache_name)


def get_session() -> CachedSession:
    """
    Get cached session with SQLite backend (default) or MongoDB (optional dev convenience).

    Environment variables:
    - CACHE_BACKEND: 'sqlite' (default) or 'mongodb'
    - CACHE_NAME: Cache file/collection name (default: 'cache/http')
    - For MongoDB: MONGO_URI (required), MONGO_DB (default: 'requests_cache'), MONGO_COLL (default: 'http')

    MongoDB gracefully falls back to SQLite if connection fails.
    """
    global _SESSION
    if _SESSION is None:
        _SESSION = _make_session()
    return _SESSION


def reset_session():
    """Close and clear the module session (for tests)."""
    global _SESSION
    try:
        if _SESSION:
            _SESSION.close()
    except Exception:
        pass
    _SESSION = None


def set_session_for_tests(session: CachedSession):
    """Force http_cache.get_session() to return a provided session (for tests)."""
    global _SESSION
    _SESSION = session


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
