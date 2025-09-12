"""
pytest configuration for biosample-enricher tests.

Ensures environment variables from .env are loaded for all tests.
"""

import os
import time
import threading
import uuid
import importlib
from pathlib import Path

import pytest
import requests_cache
from dotenv import load_dotenv


def pytest_configure(config):
    """Configure pytest session - load environment variables."""
    # Find .env file in project root (parent of tests directory)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print(f"No .env file found at {env_path}")


@pytest.fixture(scope="session", autouse=True)
def load_environment():
    """Automatically load environment variables for all tests."""
    # This fixture runs automatically for all tests
    # The actual loading is done in pytest_configure above
    pass


@pytest.fixture
def google_api_key():
    """Provide Google API key for tests that need it."""
    api_key = os.getenv("GOOGLE_MAIN_API_KEY")
    if not api_key:
        pytest.skip("Google API key not available")
    return api_key


# Google API rate limiting to prevent quota issues
_google_lock = threading.Lock()
_google_last = [0.0]


@pytest.fixture(autouse=True)
def _google_qps(request):
    """Rate limit Google API calls to prevent quota/burst issues."""
    # Only apply to tests marked with 'google' or containing google in the test path
    if not (
        "google" in request.keywords
        or "google" in str(request.fspath).lower()
        or "google" in request.node.name.lower()
    ):
        yield
        return

    with _google_lock:
        now = time.time()
        gap = 0.12 - (now - _google_last[0])  # ~8 QPS; adjust as needed
        if gap > 0:
            time.sleep(gap)
        _google_last[0] = time.time()
    yield


@pytest.fixture
def google_isolated_session(tmp_path):
    """Provide isolated cache session for Google tests to prevent cross-test contamination."""
    session_id = uuid.uuid4().hex
    return requests_cache.CachedSession(
        cache_name=str(tmp_path / f"google_{session_id}"),
        backend="sqlite",
        cache_control=True,
        allowable_codes=(200,),
        expire_after=3600,  # 1 hour for test stability
    )


@pytest.fixture(autouse=True)
def _no_global_cache():
    """Ensure no global requests-cache installation interferes with tests."""
    try:
        requests_cache.uninstall_cache()
    except Exception:
        pass
    yield
    try:
        requests_cache.uninstall_cache()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _guard_google_env(monkeypatch):
    """Protect Google API key from being cleared by other tests."""
    key = os.environ.get("GOOGLE_MAIN_API_KEY")
    if key:
        monkeypatch.setenv("GOOGLE_MAIN_API_KEY", key)
    yield


@pytest.fixture(autouse=True)
def _reset_http_cache_state():
    """Reset http_cache module globals and singletons before each test."""
    try:
        hc = importlib.import_module("biosample_enricher.http_cache")
        # Common patterns: module-level _session or get_session() memoization
        for attr in ("_session", "SESSION", "session", "cached_session"):
            if hasattr(hc, attr):
                s = getattr(hc, attr)
                try:
                    if s:
                        s.close()
                except Exception:
                    pass
                setattr(hc, attr, None)
        # Reset known flags if they exist (harmless if absent)
        for flag in ("READ_CACHE_ONLY", "OFFLINE", "WRITE_THROUGH", "FORCE_PROVIDER"):
            if hasattr(hc, flag):
                setattr(hc, flag, False)
    except Exception:
        pass
    yield


@pytest.fixture(autouse=True)
def clear_config_cache():
    """Clear both old and new config caches before each test to ensure isolation."""
    try:
        from biosample_enricher.config import clear_config_cache, clear_settings_cache

        clear_config_cache()
        clear_settings_cache()
    except ImportError:
        pass  # Functions may not exist during transition
    yield
