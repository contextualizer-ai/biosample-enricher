"""Tests for data models."""

import pytest
from pydantic import ValidationError

from biosample_enricher.models import BiosampleMetadata, EnrichmentResult


class TestBiosampleMetadata:
    """Test cases for BiosampleMetadata model."""

    def test_required_fields_only(self):
        """Test creating metadata with only required fields."""
        metadata = BiosampleMetadata(sample_id="TEST001")
        assert metadata.sample_id == "TEST001"
        assert metadata.sample_name is None
        assert metadata.organism is None
        assert metadata.metadata == {}
        assert metadata.enriched_data == {}

    def test_all_fields(self):
        """Test creating metadata with all fields."""
        metadata = BiosampleMetadata(
            sample_id="TEST001",
            sample_name="Test Sample",
            organism="Homo sapiens",
            tissue_type="blood",
            collection_date="2023-01-15",
            location="Boston, MA",
            metadata={"study": "test"},
            enriched_data={"taxonomy": "9606"},
        )
        assert metadata.sample_id == "TEST001"
        assert metadata.sample_name == "Test Sample"
        assert metadata.organism == "Homo sapiens"
        assert metadata.tissue_type == "blood"
        assert metadata.collection_date == "2023-01-15"
        assert metadata.location == "Boston, MA"
        assert metadata.metadata == {"study": "test"}
        assert metadata.enriched_data == {"taxonomy": "9606"}

    def test_missing_required_field(self):
        """Test that missing required field raises ValidationError."""
        with pytest.raises(ValidationError):
            BiosampleMetadata()

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        metadata = BiosampleMetadata(sample_id="TEST001", extra_field="extra_value")
        assert metadata.sample_id == "TEST001"
        assert hasattr(metadata, "extra_field")
        assert metadata.extra_field == "extra_value"


class TestEnrichmentResult:
    """Test cases for EnrichmentResult model."""

    def test_valid_result(self, sample_metadata):
        """Test creating a valid enrichment result."""
        enriched = sample_metadata.model_copy(deep=True)
        enriched.enriched_data = {"taxonomy": "9606"}

        result = EnrichmentResult(
            original_metadata=sample_metadata,
            enriched_metadata=enriched,
            confidence_score=0.85,
            sources=["taxonomy_db"],
            processing_time=1.5,
        )

        assert result.original_metadata == sample_metadata
        assert result.enriched_metadata == enriched
        assert result.confidence_score == 0.85
        assert result.sources == ["taxonomy_db"]
        assert result.processing_time == 1.5

    def test_confidence_score_bounds(self, sample_metadata):
        """Test confidence score validation."""
        enriched = sample_metadata.model_copy(deep=True)

        # Test valid bounds
        result = EnrichmentResult(
            original_metadata=sample_metadata,
            enriched_metadata=enriched,
            confidence_score=0.0,
            processing_time=1.0,
        )
        assert result.confidence_score == 0.0

        result = EnrichmentResult(
            original_metadata=sample_metadata,
            enriched_metadata=enriched,
            confidence_score=1.0,
            processing_time=1.0,
        )
        assert result.confidence_score == 1.0

        # Test invalid bounds
        with pytest.raises(ValidationError):
            EnrichmentResult(
                original_metadata=sample_metadata,
                enriched_metadata=enriched,
                confidence_score=-0.1,
                processing_time=1.0,
            )

        with pytest.raises(ValidationError):
            EnrichmentResult(
                original_metadata=sample_metadata,
                enriched_metadata=enriched,
                confidence_score=1.1,
                processing_time=1.0,
            )

    def test_no_extra_fields(self, sample_metadata):
        """Test that extra fields are not allowed in EnrichmentResult."""
        enriched = sample_metadata.model_copy(deep=True)

        with pytest.raises(ValidationError):
            EnrichmentResult(
                original_metadata=sample_metadata,
                enriched_metadata=enriched,
                confidence_score=0.85,
                processing_time=1.0,
                extra_field="not_allowed",
            )
