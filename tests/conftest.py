"""Pytest configuration and fixtures."""

import pytest

from biosample_enricher.core import BiosampleEnricher
from biosample_enricher.models import BiosampleMetadata


@pytest.fixture
def sample_metadata():
    """Sample biosample metadata for testing."""
    return BiosampleMetadata(
        sample_id="SAMPLE001",
        sample_name="Test Sample",
        organism="Homo sapiens",
        tissue_type="blood",
        collection_date="2023-01-15",
        location="Boston, MA",
        metadata={"study": "test_study", "batch": "A"},
    )


@pytest.fixture
def minimal_sample():
    """Minimal biosample metadata for testing."""
    return BiosampleMetadata(sample_id="MIN001")


@pytest.fixture
def enricher():
    """BiosampleEnricher instance for testing."""
    return BiosampleEnricher(api_timeout=5.0, enable_caching=True)


@pytest.fixture
def enricher_no_cache():
    """BiosampleEnricher instance without caching."""
    return BiosampleEnricher(api_timeout=5.0, enable_caching=False)
