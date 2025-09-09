"""Core functionality for biosample enrichment."""

import time
from typing import Any

from .models import BiosampleMetadata, EnrichmentResult


class BiosampleEnricher:
    """Main class for enriching biosample metadata."""

    def __init__(self, api_timeout: float = 30.0, enable_caching: bool = True) -> None:
        """Initialize the enricher.

        Args:
            api_timeout: Timeout for API calls in seconds
            enable_caching: Whether to enable caching of results
        """
        self.api_timeout = api_timeout
        self.enable_caching = enable_caching
        self._cache: dict[str, Any] = {} if enable_caching else {}

    def enrich_sample(self, sample: BiosampleMetadata) -> EnrichmentResult:
        """Enrich a single biosample with additional metadata.

        Args:
            sample: The biosample to enrich

        Returns:
            EnrichmentResult containing original and enriched metadata
        """
        start_time = time.time()

        # Cache result
        cache_key = f"{sample.sample_id}_{hash(str(sample.model_dump()))}"
        if self.enable_caching and cache_key in self._cache:
            cached_result: EnrichmentResult = self._cache[cache_key]
            cached_result.processing_time = time.time() - start_time
            return cached_result

        # Create enriched copy
        enriched_sample = sample.model_copy(deep=True)
        sources_used = []

        # Enrich with organism data
        if sample.organism:
            organism_data = self._enrich_organism_data(sample.organism)
            enriched_sample.enriched_data.update(organism_data)
            if organism_data:
                sources_used.append("organism_database")

        # Enrich with location data
        if sample.location:
            location_data = self._enrich_location_data(sample.location)
            enriched_sample.enriched_data.update(location_data)
            if location_data:
                sources_used.append("location_database")

        # Calculate confidence score based on available data
        confidence = self._calculate_confidence(sample, enriched_sample)

        processing_time = time.time() - start_time

        result = EnrichmentResult(
            original_metadata=sample,
            enriched_metadata=enriched_sample,
            confidence_score=confidence,
            sources=sources_used,
            processing_time=processing_time,
        )

        # Cache result
        if self.enable_caching:
            self._cache[cache_key] = result

        return result

    def enrich_samples(
        self, samples: list[BiosampleMetadata]
    ) -> list[EnrichmentResult]:
        """Enrich multiple biosamples.

        Args:
            samples: List of biosamples to enrich

        Returns:
            List of enrichment results
        """
        return [self.enrich_sample(sample) for sample in samples]

    def _enrich_organism_data(self, organism: str) -> dict[str, Any]:
        """Enrich organism data from external sources.

        Args:
            organism: Organism name

        Returns:
            Dictionary of enriched organism data
        """
        # Mock enrichment - in real implementation, this would query databases
        organism_data = {
            "organism_taxonomy": f"taxonomy_for_{organism.lower().replace(' ', '_')}",
            "organism_kingdom": "Unknown",
            "organism_phylum": "Unknown",
        }

        # Simulate some basic taxonomy enrichment
        if "homo sapiens" in organism.lower():
            organism_data.update(
                {
                    "organism_kingdom": "Animalia",
                    "organism_phylum": "Chordata",
                    "organism_class": "Mammalia",
                }
            )
        elif "escherichia" in organism.lower():
            organism_data.update(
                {
                    "organism_kingdom": "Bacteria",
                    "organism_phylum": "Proteobacteria",
                    "organism_class": "Gammaproteobacteria",
                }
            )

        return organism_data

    def _enrich_location_data(self, location: str) -> dict[str, Any]:
        """Enrich location data from external sources.

        Args:
            location: Location string

        Returns:
            Dictionary of enriched location data
        """
        # Mock enrichment - in real implementation, this would query geo databases
        return {
            "location_normalized": location.title(),
            "location_type": "geographic",
            "location_coordinates": None,  # Would be populated from geocoding API
        }

    def _calculate_confidence(
        self, original: BiosampleMetadata, enriched: BiosampleMetadata
    ) -> float:
        """Calculate confidence score for enrichment.

        Args:
            original: Original metadata
            enriched: Enriched metadata

        Returns:
            Confidence score between 0 and 1
        """
        # Simple confidence calculation based on data completeness
        original_fields = len(
            [
                v
                for v in original.model_dump().values()
                if v is not None and v != {} and v != []
            ]
        )
        enriched_fields = len(
            [v for v in enriched.enriched_data.values() if v is not None]
        )

        if original_fields == 0:
            return 0.0

        # Base confidence on original data quality and enrichment amount
        base_confidence = min(original_fields / 10.0, 1.0)  # Normalize to max 1.0
        enrichment_bonus = min(enriched_fields / 20.0, 0.3)  # Max 30% bonus

        return min(base_confidence + enrichment_bonus, 1.0)

    def clear_cache(self) -> None:
        """Clear the enrichment cache."""
        self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {"cache_size": len(self._cache), "cache_enabled": self.enable_caching}
