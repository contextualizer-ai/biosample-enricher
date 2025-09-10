"""
Simple HTTP caching with coordinate canonicalization using requests-cache.
"""

import os
from typing import Any

import requests
import requests_cache
from requests_cache import CachedSession

from .logging_config import get_logger

logger = get_logger(__name__)


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
            from pymongo import MongoClient

            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            logger.debug(f"Attempting MongoDB connection to {mongo_uri}")
            client: MongoClient = MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
            client.admin.command("ping")  # Test connection
            backend = requests_cache.MongoCache(db_name="http_cache", connection=client)
            logger.info("Using MongoDB cache backend")
        except Exception as e:
            # Fall back to SQLite if MongoDB unavailable
            logger.warning(f"MongoDB unavailable, falling back to SQLite: {e}")
            backend = requests_cache.SQLiteCache("http_cache")

    return CachedSession(backend=backend)


def request(method: str, url: str, **kwargs: Any) -> requests.Response:
    """Make cached HTTP request with coordinate canonicalization."""
    # Canonicalize coordinates in params
    if "params" in kwargs:
        original_params = kwargs["params"].copy() if kwargs["params"] else {}
        kwargs["params"] = canonicalize_coords(kwargs["params"])
        if original_params != kwargs["params"]:
            logger.debug(
                f"Canonicalized coordinates: {original_params} -> {kwargs['params']}"
            )

    logger.debug(f"Making {method} request to {url}")
    session = get_session()
    response = session.request(method, url, **kwargs)

    cache_status = "HIT" if getattr(response, "from_cache", False) else "MISS"
    logger.debug(f"{method} {url} -> {response.status_code} (Cache: {cache_status})")

    return response
