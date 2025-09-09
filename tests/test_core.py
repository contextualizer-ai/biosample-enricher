"""Tests for the core biosample enricher functionality."""

from unittest.mock import Mock, patch

import pytest

from biosample_enricher.core import BiosampleEnricher, BiosampleMetadata


class TestBiosampleMetadata:
    """Test the BiosampleMetadata model."""

    def test_metadata_creation(self) -> None:
        """Test creating a BiosampleMetadata instance."""
        metadata = BiosampleMetadata(
            sample_id="SAMN123456",
            source="ncbi",
            metadata={"organism": "Homo sapiens"},
            confidence=0.9,
        )

        assert metadata.sample_id == "SAMN123456"
        assert metadata.source == "ncbi"
        assert metadata.metadata == {"organism": "Homo sapiens"}
        assert metadata.confidence == 0.9

    def test_metadata_defaults(self) -> None:
        """Test default values for BiosampleMetadata."""
        metadata = BiosampleMetadata(sample_id="SAMN123456", source="ncbi")

        assert metadata.metadata == {}
        assert metadata.confidence == 0.0

    def test_confidence_validation(self) -> None:
        """Test confidence score validation."""
        # Valid confidence scores
        metadata1 = BiosampleMetadata(
            sample_id="SAMN123456", source="ncbi", confidence=0.0
        )
        assert metadata1.confidence == 0.0

        metadata2 = BiosampleMetadata(
            sample_id="SAMN123456", source="ncbi", confidence=1.0
        )
        assert metadata2.confidence == 1.0

        # Invalid confidence scores should raise validation error
        with pytest.raises(ValueError):
            BiosampleMetadata(sample_id="SAMN123456", source="ncbi", confidence=-0.1)

        with pytest.raises(ValueError):
            BiosampleMetadata(sample_id="SAMN123456", source="ncbi", confidence=1.1)


class TestBiosampleEnricher:
    """Test the BiosampleEnricher class."""

    def test_init(self) -> None:
        """Test BiosampleEnricher initialization."""
        enricher = BiosampleEnricher(timeout=60.0)
        assert enricher.timeout == 60.0
        enricher.close()

    def test_context_manager(self) -> None:
        """Test using BiosampleEnricher as a context manager."""
        with BiosampleEnricher() as enricher:
            assert enricher.timeout == 30.0

    @patch("biosample_enricher.core.BiosampleEnricher._fetch_metadata")
    def test_enrich_sample(self, mock_fetch: Mock) -> None:
        """Test enriching a single sample."""
        mock_metadata = BiosampleMetadata(
            sample_id="SAMN123456",
            source="ncbi",
            metadata={"organism": "Homo sapiens"},
            confidence=0.85,
        )
        mock_fetch.return_value = mock_metadata

        with BiosampleEnricher() as enricher:
            results = enricher.enrich_sample("SAMN123456", ["ncbi"])

        assert len(results) == 1
        assert results[0].sample_id == "SAMN123456"
        assert results[0].source == "ncbi"
        mock_fetch.assert_called_once_with("SAMN123456", "ncbi")

    @patch("biosample_enricher.core.BiosampleEnricher._fetch_metadata")
    def test_enrich_sample_default_sources(self, mock_fetch: Mock) -> None:
        """Test enriching a sample with default sources."""
        mock_metadata = BiosampleMetadata(
            sample_id="SAMN123456",
            source="ncbi",
            metadata={},
            confidence=0.85,
        )
        mock_fetch.return_value = mock_metadata

        with BiosampleEnricher() as enricher:
            results = enricher.enrich_sample("SAMN123456")

        # Should call with default sources
        assert len(results) == 3  # ncbi, ebi, biosample_db
        assert mock_fetch.call_count == 3

    @patch("biosample_enricher.core.BiosampleEnricher._fetch_metadata")
    def test_enrich_sample_with_error(self, mock_fetch: Mock) -> None:
        """Test enriching a sample when one source fails."""
        mock_fetch.side_effect = [
            BiosampleMetadata(
                sample_id="SAMN123456",
                source="ncbi",
                metadata={"organism": "Homo sapiens"},
                confidence=0.85,
            ),
            Exception("API error"),
        ]

        with BiosampleEnricher() as enricher:
            results = enricher.enrich_sample("SAMN123456", ["ncbi", "ebi"])

        # Should return only successful results
        assert len(results) == 1
        assert results[0].source == "ncbi"

    def test_fetch_metadata(self) -> None:
        """Test the _fetch_metadata method."""
        with BiosampleEnricher() as enricher:
            metadata = enricher._fetch_metadata("SAMN123456", "ncbi")

        assert metadata.sample_id == "SAMN123456"
        assert metadata.source == "ncbi"
        assert metadata.confidence == 0.85
        assert "organism" in metadata.metadata
        assert "source_specific_field" in metadata.metadata

    @patch("biosample_enricher.core.BiosampleEnricher.enrich_sample")
    def test_enrich_multiple(self, mock_enrich: Mock) -> None:
        """Test enriching multiple samples."""
        mock_metadata = BiosampleMetadata(
            sample_id="SAMN123456",
            source="ncbi",
            metadata={},
            confidence=0.85,
        )
        mock_enrich.return_value = [mock_metadata]

        with BiosampleEnricher() as enricher:
            results = enricher.enrich_multiple(["SAMN123456", "SAMN789012"])

        assert len(results) == 2
        assert "SAMN123456" in results
        assert "SAMN789012" in results
        assert mock_enrich.call_count == 2


@pytest.fixture
def sample_metadata() -> BiosampleMetadata:
    """Fixture providing sample metadata for tests."""
    return BiosampleMetadata(
        sample_id="SAMN123456",
        source="ncbi",
        metadata={
            "organism": "Homo sapiens",
            "tissue": "blood",
            "collection_date": "2023-01-01",
        },
        confidence=0.9,
    )


def test_sample_metadata_fixture(sample_metadata: BiosampleMetadata) -> None:
    """Test the sample metadata fixture."""
    assert sample_metadata.sample_id == "SAMN123456"
    assert sample_metadata.source == "ncbi"
    assert sample_metadata.confidence == 0.9
