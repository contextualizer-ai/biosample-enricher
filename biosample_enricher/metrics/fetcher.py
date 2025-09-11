"""Fetcher for random biosample data for metrics evaluation.

This module leverages existing adapters and fetchers to retrieve
random samples from NMDC and GOLD databases for coverage analysis.
"""

from typing import Any

from biosample_enricher.adapters import (
    MongoGOLDBiosampleFetcher,
    MongoNMDCBiosampleFetcher,
)
from biosample_enricher.logging_config import get_logger
from biosample_enricher.models import BiosampleLocation

logger = get_logger(__name__)


class BiosampleMetricsFetcher:
    """Fetcher for retrieving random biosamples for metrics evaluation."""

    def __init__(
        self,
        nmdc_connection_string: str | None = None,
        gold_connection_string: str | None = None,
        nmdc_database: str = "nmdc",
        gold_database: str = "gold_metadata",
        nmdc_collection: str = "biosample_set",
        gold_collection: str = "biosamples",
    ):
        """Initialize metrics fetcher with database connections.

        Args:
            nmdc_connection_string: MongoDB connection string for NMDC
            gold_connection_string: MongoDB connection string for GOLD
            nmdc_database: NMDC database name
            gold_database: GOLD database name
            nmdc_collection: NMDC collection name
            gold_collection: GOLD collection name
        """
        self.nmdc_fetcher = MongoNMDCBiosampleFetcher(
            connection_string=nmdc_connection_string,
            database_name=nmdc_database,
            collection_name=nmdc_collection,
        )

        self.gold_fetcher = MongoGOLDBiosampleFetcher(
            connection_string=gold_connection_string,
            database_name=gold_database,
            collection_name=gold_collection,
        )

    def fetch_nmdc_samples(
        self, n: int = 100, enrichable_only: bool = False
    ) -> tuple[list[dict[str, Any]], list[BiosampleLocation]]:
        """Fetch random NMDC samples.

        Args:
            n: Number of samples to fetch
            enrichable_only: Whether to fetch only samples with coordinates

        Returns:
            Tuple of (raw documents, normalized locations)
        """
        logger.info(
            f"Fetching {n} random NMDC samples (enrichable_only={enrichable_only})"
        )

        if not self.nmdc_fetcher.connect():
            logger.error("Failed to connect to NMDC database")
            return [], []

        try:
            # Get raw documents and normalized locations
            raw_docs = []
            locations = []

            if enrichable_only:
                fetched = self.nmdc_fetcher.fetch_random_enrichable_locations(n)
            else:
                fetched = self.nmdc_fetcher.fetch_random_locations(n)

            # We need to fetch twice to get both raw and normalized
            # First pass: get locations
            locations = list(fetched)

            # Second pass: get raw documents using the IDs (preserving order)
            if locations:
                ids = [loc.sample_id for loc in locations if loc.sample_id]
                if ids:
                    # Fetch raw documents by IDs, preserving the order of locations
                    cursor = self.nmdc_fetcher._collection.find({"id": {"$in": ids}})
                    docs_by_id = {doc["id"]: doc for doc in cursor}
                    # Rebuild raw_docs in the same order as locations
                    raw_docs = [
                        docs_by_id[sample_id]
                        for sample_id in ids
                        if sample_id in docs_by_id
                    ]

            logger.info(f"Retrieved {len(locations)} NMDC samples")
            return raw_docs, locations

        finally:
            self.nmdc_fetcher.disconnect()

    def fetch_gold_samples(
        self, n: int = 100, enrichable_only: bool = False
    ) -> tuple[list[dict[str, Any]], list[BiosampleLocation]]:
        """Fetch random GOLD samples.

        Args:
            n: Number of samples to fetch
            enrichable_only: Whether to fetch only samples with coordinates

        Returns:
            Tuple of (raw documents, normalized locations)
        """
        logger.info(
            f"Fetching {n} random GOLD samples (enrichable_only={enrichable_only})"
        )

        if not self.gold_fetcher.connect():
            logger.error("Failed to connect to GOLD database")
            return [], []

        try:
            # Get raw documents and normalized locations
            raw_docs = []
            locations = []

            if enrichable_only:
                fetched = self.gold_fetcher.fetch_random_enrichable_locations(n)
            else:
                fetched = self.gold_fetcher.fetch_random_locations(n)

            # We need to fetch twice to get both raw and normalized
            # First pass: get locations
            locations = list(fetched)

            # Second pass: get raw documents using the IDs (preserving order)
            if locations:
                ids = [loc.sample_id for loc in locations if loc.sample_id]
                if ids:
                    # Fetch raw documents by IDs, preserving the order of locations
                    cursor = self.gold_fetcher._collection.find(
                        {"biosampleGoldId": {"$in": ids}}
                    )
                    docs_by_id = {doc["biosampleGoldId"]: doc for doc in cursor}
                    # Rebuild raw_docs in the same order as locations
                    raw_docs = [
                        docs_by_id[sample_id]
                        for sample_id in ids
                        if sample_id in docs_by_id
                    ]

            logger.info(f"Retrieved {len(locations)} GOLD samples")
            return raw_docs, locations

        finally:
            self.gold_fetcher.disconnect()

    def fetch_all_samples(
        self, n_per_source: int = 100, enrichable_only: bool = False
    ) -> dict[str, tuple[list[dict[str, Any]], list[BiosampleLocation]]]:
        """Fetch random samples from both NMDC and GOLD.

        Args:
            n_per_source: Number of samples to fetch from each source
            enrichable_only: Whether to fetch only samples with coordinates

        Returns:
            Dictionary with 'nmdc' and 'gold' keys containing tuples of
            (raw documents, normalized locations)
        """
        return {
            "nmdc": self.fetch_nmdc_samples(n_per_source, enrichable_only),
            "gold": self.fetch_gold_samples(n_per_source, enrichable_only),
        }
