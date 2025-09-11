"""
pytest configuration for biosample-enricher tests.

Ensures environment variables from .env are loaded for all tests.
"""

import os
from pathlib import Path

import pytest
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
