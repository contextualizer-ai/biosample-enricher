"""
MongoDB-based HTTP Caching System

Centralized HTTP caching with MongoDB backend that supports:
- Input canonicalization (lat/lon rounding, datetime truncation)
- Per-call cache control (read_from_cache, write_to_cache)
- Cache inspection and management
- Integration with requests
"""

import hashlib
import json
import os
import re
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pymongo
import requests
from pydantic import BaseModel
from pymongo import MongoClient

if TYPE_CHECKING:
    from pymongo.collection import Collection


class CacheEntry(BaseModel):
    """Model for cache entries stored in MongoDB."""

    cache_key: str
    url: str
    method: str
    headers: dict[str, str]
    request_body: bytes | None = None
    status_code: int
    response_headers: dict[str, str]
    response_body: bytes
    created_at: datetime
    expires_at: datetime | None = None
    hit_count: int = 0
    last_accessed: datetime


class RequestCanonicalizer:
    """Handles input canonicalization for consistent cache keys."""

    def __init__(self, coord_precision: int = 4, truncate_dates: bool = True):
        self.coord_precision = coord_precision
        self.truncate_dates = truncate_dates

    def _round_coord(self, value: Any) -> Any:
        """Round coordinate to specified precision."""
        try:
            return None if value is None else round(float(value), self.coord_precision)
        except (ValueError, TypeError):
            return value

    def _truncate_datetime(self, value: Any) -> Any:
        """Convert datetime-like values to YYYY-MM-DD format."""
        if not self.truncate_dates:
            return value

        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()

        # Try to parse ISO-like strings
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "").replace("T", " "))
                return dt.date().isoformat()
            except (ValueError, TypeError):
                pass

        return value

    def canonicalize_params(self, params: dict[str, Any] | None) -> dict[str, Any]:
        """Canonicalize query parameters."""
        if not params:
            return {}

        canonical = {}
        for key, value in params.items():
            key_lower = key.lower()

            # Handle coordinates
            if key_lower in {"lat", "latitude"} or key_lower in {
                "lon",
                "lng",
                "longitude",
            }:
                canonical[key] = self._round_coord(value)
            # Handle date/time fields
            elif "date" in key_lower or "time" in key_lower:
                canonical[key] = self._truncate_datetime(value)
            else:
                canonical[key] = value

        return canonical

    def canonicalize_url(self, url: str) -> str:
        """Canonicalize URL by rounding embedded coordinates and normalizing dates."""
        parts = urlsplit(url)
        path = parts.path

        # Round lat,lon pairs in path (e.g., /points/{lat},{lon})
        def _path_round(match: re.Match[str]) -> str:
            lat, lon = float(match.group(1)), float(match.group(2))
            return (
                f"{round(lat, self.coord_precision)},{round(lon, self.coord_precision)}"
            )

        path = re.sub(r"(-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)", _path_round, path)

        # Handle query parameters in URL
        query_params = parse_qsl(parts.query, keep_blank_values=True)
        canonical_params = []

        for key, value in query_params:
            key_lower = key.lower()
            if key_lower in {"lat", "latitude"} or key_lower in {
                "lon",
                "lng",
                "longitude",
            }:
                value = str(self._round_coord(value))
            elif "date" in key_lower or "time" in key_lower:
                value = str(self._truncate_datetime(value))

            canonical_params.append((key, value))

        canonical_query = urlencode(canonical_params, doseq=True)
        return urlunsplit(
            (parts.scheme, parts.netloc, path, canonical_query, parts.fragment)
        )


class MongoHTTPCache:
    """MongoDB-based HTTP cache backend."""

    def __init__(
        self,
        mongo_uri: str,
        database: str = "http_cache",
        collection: str = "requests",
        default_expire_after: int | None = None,  # seconds
        coord_precision: int = 4,
        truncate_dates: bool = True,
    ):
        self.mongo_uri = mongo_uri
        self.database_name = database
        self.collection_name = collection
        self.default_expire_after = default_expire_after

        self.canonicalizer = RequestCanonicalizer(coord_precision, truncate_dates)
        self._client: MongoClient | None = None
        self._collection: Collection | None = None
        self._connect()

    def _connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            self._client = MongoClient(self.mongo_uri)
            # Test connection
            self._client.admin.command("ping")
            db = self._client[self.database_name]
            self._collection = db[self.collection_name]

            # Create indexes for efficient querying
            self._collection.create_index(
                [("cache_key", pymongo.ASCENDING)], unique=True
            )
            self._collection.create_index([("created_at", pymongo.DESCENDING)])
            self._collection.create_index([("expires_at", pymongo.ASCENDING)])
            self._collection.create_index(
                [("url", pymongo.ASCENDING), ("method", pymongo.ASCENDING)]
            )

        except Exception as e:
            print(f"Warning: MongoDB cache unavailable: {e}")
            self._client = None
            self._collection = None

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (UTC)."""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            return dt.replace(tzinfo=UTC)
        return dt

    def _generate_cache_key(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        body: bytes | None = None,
    ) -> str:
        """Generate a consistent cache key."""
        # Canonicalize URL and params
        canonical_url = self.canonicalizer.canonicalize_url(url)
        canonical_params = self.canonicalizer.canonicalize_params(params)

        # Create cache key components
        key_data = {
            "method": method.upper(),
            "url": canonical_url,
            "params": canonical_params,
            "body_hash": hashlib.sha256(body or b"").hexdigest()[:16],
        }

        # Generate consistent hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        body: bytes | None = None,
    ) -> CacheEntry | None:
        """Retrieve cached response."""
        if self._collection is None:
            return None

        cache_key = self._generate_cache_key(method, url, params, body)

        try:
            doc = self._collection.find_one({"cache_key": cache_key})
            if not doc:
                return None

            # Check expiration
            now = datetime.now(UTC)
            expires_at = doc.get("expires_at")
            if expires_at and self._ensure_timezone_aware(expires_at) < now:
                # Expired, remove it
                self._collection.delete_one({"cache_key": cache_key})
                return None

            # Update access statistics
            self._collection.update_one(
                {"cache_key": cache_key},
                {"$inc": {"hit_count": 1}, "$set": {"last_accessed": now}},
            )

            # Ensure timezone-aware datetimes in doc
            if "created_at" in doc:
                doc["created_at"] = self._ensure_timezone_aware(doc["created_at"])
            if "expires_at" in doc and doc["expires_at"]:
                doc["expires_at"] = self._ensure_timezone_aware(doc["expires_at"])
            if "last_accessed" in doc:
                doc["last_accessed"] = self._ensure_timezone_aware(doc["last_accessed"])

            return CacheEntry(**doc)

        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None

    def set(
        self,
        method: str,
        url: str,
        response: requests.Response,
        params: dict[str, Any] | None = None,
        body: bytes | None = None,
        expire_after: int | None = None,
    ) -> None:
        """Store response in cache."""
        if self._collection is None:
            return

        cache_key = self._generate_cache_key(method, url, params, body)
        now = datetime.now(UTC)

        # Determine expiration
        expires_at = None
        ttl = expire_after if expire_after is not None else self.default_expire_after
        if ttl:
            expires_at = now + timedelta(seconds=ttl)

        entry = CacheEntry(
            cache_key=cache_key,
            url=url,
            method=method.upper(),
            headers=dict(response.request.headers) if response.request else {},
            request_body=body,
            status_code=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.content,
            created_at=now,
            expires_at=expires_at,
            hit_count=0,
            last_accessed=now,
        )

        try:
            # Upsert the cache entry
            self._collection.replace_one(
                {"cache_key": cache_key}, entry.model_dump(), upsert=True
            )
        except Exception as e:
            print(f"Cache storage error: {e}")

    def delete(self, cache_key: str) -> bool:
        """Delete specific cache entry."""
        if self._collection is None:
            return False

        try:
            result = self._collection.delete_one({"cache_key": cache_key})
            return result.deleted_count > 0
        except Exception:
            return False

    def clear(self, older_than_hours: int | None = None) -> int:
        """Clear cache entries."""
        if self._collection is None:
            return 0

        try:
            if older_than_hours:
                cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
                result = self._collection.delete_many({"created_at": {"$lt": cutoff}})
            else:
                result = self._collection.delete_many({})

            return result.deleted_count
        except Exception:
            return 0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if self._collection is None:
            return {"error": "Cache unavailable"}

        try:
            total_entries = self._collection.count_documents({})

            # Count by status code
            status_pipeline: list[dict[str, Any]] = [
                {"$group": {"_id": "$status_code", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
            status_counts = list(self._collection.aggregate(status_pipeline))

            # Count by method
            method_pipeline: list[dict[str, Any]] = [
                {"$group": {"_id": "$method", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
            method_counts = list(self._collection.aggregate(method_pipeline))

            # Get total hits
            total_hits = list(
                self._collection.aggregate(
                    [{"$group": {"_id": None, "total_hits": {"$sum": "$hit_count"}}}]
                )
            )

            # Recent activity (last 24 hours)
            recent_cutoff = datetime.now(UTC) - timedelta(hours=24)
            recent_count = self._collection.count_documents(
                {"created_at": {"$gte": recent_cutoff}}
            )

            return {
                "total_entries": total_entries,
                "total_hits": total_hits[0]["total_hits"] if total_hits else 0,
                "recent_entries_24h": recent_count,
                "by_status_code": {
                    item["_id"]: item["count"] for item in status_counts
                },
                "by_method": {item["_id"]: item["count"] for item in method_counts},
            }
        except Exception as e:
            return {"error": str(e)}

    def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()


class CachedHTTPClient:
    """HTTP client with MongoDB caching capabilities."""

    def __init__(
        self,
        cache: MongoHTTPCache | None = None,
        mongo_uri: str | None = None,
        **cache_kwargs: Any,
    ) -> None:
        self.cache: MongoHTTPCache | None
        if cache:
            self.cache = cache
        elif mongo_uri:
            self.cache = MongoHTTPCache(mongo_uri, **cache_kwargs)
        else:
            # Try to get from environment
            mongo_uri = os.getenv("MONGO_URI")
            if mongo_uri:
                self.cache = MongoHTTPCache(mongo_uri, **cache_kwargs)
            else:
                self.cache = None

        self.session = requests.Session()

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        content: bytes | None = None,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        expire_after: int | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Make HTTP request with caching support.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            json: JSON body data
            data: Form data
            content: Raw content
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            expire_after: Cache expiration in seconds
            **kwargs: Additional requests arguments

        Returns:
            requests.Response object
        """
        # Prepare request body
        body = None
        if content:
            body = content
        elif json is not None:
            import json as json_module

            body = json_module.dumps(json, sort_keys=True).encode()
        elif data:
            # For form data, create a consistent representation
            if isinstance(data, dict):
                body = urlencode(sorted(data.items())).encode()
            else:
                body = str(data).encode()

        # Try cache first if enabled
        if self.cache and read_from_cache:
            cached = self.cache.get(method, url, params, body)
            if cached:
                # Create a mock response from cache
                response = requests.Response()
                response.status_code = cached.status_code
                response.headers.update(cached.response_headers)
                response._content = cached.response_body

                # Create a mock request
                request = requests.Request(method.upper(), url, params=params)
                response.request = request.prepare()

                # Mark as from cache
                response._from_cache = True  # type: ignore[attr-defined]
                return response

        # Make actual request
        if read_from_cache and not write_to_cache:
            # Cache miss and don't want to write - make request without caching
            pass

        # Prepare request arguments
        request_kwargs = kwargs.copy()
        if params:
            request_kwargs["params"] = params
        if json is not None:
            request_kwargs["json"] = json
        elif data is not None:
            request_kwargs["data"] = data
        elif content is not None:
            # For requests, content should be passed as data
            request_kwargs["data"] = content

        response = self.session.request(method, url, **request_kwargs)

        # Cache the response if enabled
        if self.cache and write_to_cache and response.status_code < 400:
            self.cache.set(method, url, response, params, body, expire_after)

        response._from_cache = False  # type: ignore[attr-defined]
        return response

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Make GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Make POST request."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        """Make PUT request."""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        """Make DELETE request."""
        return self.request("DELETE", url, **kwargs)

    def close(self) -> None:
        """Close client and cache connections."""
        self.session.close()
        if self.cache:
            self.cache.close()

    def __enter__(self) -> "CachedHTTPClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


# Global cached client instance
_client: CachedHTTPClient | None = None


def get_cached_client(
    mongo_uri: str | None = None, **cache_kwargs: Any
) -> CachedHTTPClient:
    """Get or create global cached HTTP client."""
    global _client
    if _client is None:
        _client = CachedHTTPClient(mongo_uri=mongo_uri, **cache_kwargs)
    return _client


# Convenience functions that match the interface from the GPT example
def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    read_from_cache: bool = True,
    write_to_cache: bool = True,
    expire_after: int | None = None,
    **kwargs: Any,
) -> requests.Response:
    """
    Unified request function with cache controls and input canonicalization.

    Cache behavior:
    - True/True: Normal cached request (read & write)
    - True/False: Prefer cache; on miss, fetch fresh but don't write
    - False/True: Fetch fresh and update cache (force refresh)
    - False/False: Pure passthrough (no read, no write)
    """
    client = get_cached_client()
    return client.request(
        method,
        url,
        params=params,
        json=json,
        read_from_cache=read_from_cache,
        write_to_cache=write_to_cache,
        expire_after=expire_after,
        **kwargs,
    )


def clear_http_cache(older_than_hours: int | None = None) -> int:
    """Clear HTTP cache entries."""
    client = get_cached_client()
    if client.cache:
        return client.cache.clear(older_than_hours)
    return 0


def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics."""
    client = get_cached_client()
    if client.cache:
        return client.cache.stats()
    return {"error": "Cache not available"}
