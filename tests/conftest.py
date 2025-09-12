"""
pytest configuration for biosample-enricher tests.

Ensures environment variables from .env are loaded for all tests.
"""

import os
import uuid
import importlib
import threading
import time
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


# Session isolation harness to prevent test state leakage

@pytest.fixture(autouse=True)
def _reset_http_cache_state():
    """Reset the http_cache module's singleton & any flags between tests."""
    try:
        hc = importlib.import_module("biosample_enricher.http_cache")
        # Reset the singleton session every test (cheap; disk cache still gives speed)
        if hasattr(hc, "reset_session"):
            hc.reset_session()
        # Defensive: turn off any module flags if they exist
        for flag in ("READ_CACHE_ONLY", "OFFLINE", "WRITE_THROUGH", "FORCE_PROVIDER"):
            if hasattr(hc, flag):
                setattr(hc, flag, False)
    except Exception:
        pass
    yield


@pytest.fixture(autouse=True)
def _guard_google_env(monkeypatch):
    """Guard critical env (prevents stray patch.dict(clear=True) from nuking keys)."""
    key = os.environ.get("GOOGLE_MAIN_API_KEY")
    if key:
        monkeypatch.setenv("GOOGLE_MAIN_API_KEY", key)
    yield


@pytest.fixture(autouse=True)
def _ban_global_requests_cache():
    """Ensure no one globally monkey-patches requests via install_cache()."""
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
def _google_isolated_session(request, monkeypatch, tmp_path):
    """Automatically route *Google* tests to an isolated cache namespace."""
    node_text = (str(getattr(request, "fspath", "")).lower() + "::" + request.node.name.lower())
    if "google" not in node_text:
        yield
        return
    
    sid = uuid.uuid4().hex
    session = requests_cache.CachedSession(
        cache_name=str(tmp_path / f"google_{sid}"),
        backend="sqlite",
        cache_control=True,
        allowable_codes=(200,),
        expire_after=3600,
    )
    
    import biosample_enricher.http_cache as hc
    # Make the app use this isolated session for the duration of the test
    monkeypatch.setattr(hc, "get_session", lambda: session, raising=True)
    yield
    try: 
        session.close()
    except Exception: 
        pass


# Gentle QPS guard for Google tests only (won't slow unit tests)
_google_lock = threading.Lock()
_google_last = [0.0]

@pytest.fixture(autouse=True)
def _google_qps(request):
    """Gentle QPS guard for Google tests only."""
    node_text = (str(getattr(request, "fspath", "")).lower() + "::" + request.node.name.lower())
    if "google" not in node_text:
        yield
        return
    with _google_lock:
        now = time.time()
        gap = 0.12 - (now - _google_last[0])  # ~8 QPS; tune if needed
        if gap > 0:
            time.sleep(gap)
        _google_last[0] = time.time()
    yield


@pytest.fixture(autouse=True)
def _route_all_test_cache_to_tmp(tmp_path, monkeypatch):
    """Route all test cache to temp directory to preserve existing cache."""
    # Opt-out toggle: set USE_PROD_CACHE_IN_TESTS=1 to skip redirection
    if os.getenv("USE_PROD_CACHE_IN_TESTS"):
        yield
        return

    # Import here to avoid import-time issues
    import biosample_enricher.http_cache as hc
    
    # Start from a fresh module session
    if hasattr(hc, "reset_session"):
        hc.reset_session()

    # Build a test-only cache namespace on disk (fast & isolated)
    test_session = requests_cache.CachedSession(
        cache_name=str(tmp_path / "test_cache"),
        backend="sqlite",
        cache_control=True,
        allowable_codes=(200,),
    )
    
    # Replace the global session before test execution
    original_session = hc._SESSION
    hc._SESSION = test_session
    
    yield

    # Restore original session
    hc._SESSION = original_session
    try:
        test_session.close()
    except Exception:
        pass
