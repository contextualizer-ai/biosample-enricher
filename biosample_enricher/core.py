"""Core biosample enrichment functionality."""

from typing import Any

from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class BiosampleMetadata(BaseModel):
    """Model for biosample metadata."""

    sample_id: str = Field(description="Unique identifier for the biosample")
    source: str = Field(description="Data source for this metadata")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Enriched metadata dictionary"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score for the metadata"
    )


class BiosampleEnricher:
    """Main class for enriching biosample metadata."""

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize the biosample enricher.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout

    def __enter__(self) -> "BiosampleEnricher":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        pass

    def enrich_sample(
        self, sample_id: str, sources: list[str] | None = None
    ) -> list[BiosampleMetadata]:
        """Enrich a single biosample with metadata from multiple sources.

        Args:
            sample_id: The biosample identifier to enrich
            sources: List of data sources to query (if None, uses all available)

        Returns:
            List of metadata objects from different sources
        """
        if sources is None:
            sources = ["ncbi", "ebi", "biosample_db"]

        results = []
        for source in sources:
            try:
                metadata = self._fetch_metadata(sample_id, source)
                results.append(metadata)
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Failed to fetch from {source}: {e}[/yellow]"
                )

        return results

    def _fetch_metadata(self, sample_id: str, source: str) -> BiosampleMetadata:
        """Fetch metadata from a specific source.

        Args:
            sample_id: The biosample identifier
            source: The data source to query

        Returns:
            Metadata object with enriched information
        """
        # Placeholder implementation - would contain actual API calls
        mock_metadata = {
            "organism": "Homo sapiens",
            "tissue": "blood",
            "collection_date": "2023-01-01",
            "source_specific_field": f"data_from_{source}",
        }

        return BiosampleMetadata(
            sample_id=sample_id,
            source=source,
            metadata=mock_metadata,
            confidence=0.85,
        )

    def enrich_multiple(
        self, sample_ids: list[str], sources: list[str] | None = None
    ) -> dict[str, list[BiosampleMetadata]]:
        """Enrich multiple biosamples.

        Args:
            sample_ids: List of biosample identifiers to enrich
            sources: List of data sources to query

        Returns:
            Dictionary mapping sample IDs to their metadata lists
        """
        results = {}
        for sample_id in sample_ids:
            results[sample_id] = self.enrich_sample(sample_id, sources)

        return results

    def close(self) -> None:
        """Close resources (no-op with simplified client)."""
        pass
