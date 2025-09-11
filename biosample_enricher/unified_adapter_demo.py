#!/usr/bin/env python3
"""
Unified Biosample Adapter Demonstration

Tests the unified interface that combines NMDC and GOLD adapters:
- UnifiedBiosampleFetcher configuration
- Multi-source statistics aggregation
- Cross-database enrichment analysis
- Combined sampling strategies
"""

import json
import random
import sys
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import click

from .adapters import (
    GOLDBiosampleAdapter,
    NMDCBiosampleAdapter,
    UnifiedBiosampleFetcher,
)
from .models import BiosampleLocation


def get_sample_nmdc_biosamples() -> list[dict[str, Any]]:
    """Get sample NMDC biosamples for demonstration."""
    return [
        {
            "id": "nmdc:bsm-11-34xj1150",
            "lat_lon": "42.3601 -71.0928",
            "collection_date": {
                "has_raw_value": "2014-11-25",
                "type": "nmdc:TimestampValue",
            },
            "geo_loc_name": {
                "has_raw_value": "USA: Massachusetts, Boston Harbor",
                "type": "nmdc:TextValue",
            },
            "associated_studies": ["nmdc:sty-11-34xj1150"],
            "_id": "nmdc_001",
        },
        {
            "id": "nmdc:bsm-11-45ky2260",
            "lat_lon": {"latitude": 38.8895, "longitude": -77.0501},
            "collection_date": "2015-06-15T14:30:00Z",
            "geographic_location": "USA: Washington DC, Potomac River",
            "_id": "nmdc_002",
        },
        {
            "id": "nmdc:bsm-11-56lz3370",
            "collection_date": "2016-08-20",
            "sample_collection_site": "Land sample without coordinates",
            "_id": "nmdc_003",
        },
    ]


def get_sample_gold_biosamples() -> list[dict[str, Any]]:
    """Get sample GOLD biosamples for demonstration."""
    return [
        {
            "biosampleGoldId": "Gb0115231",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "dateCollected": "2016-03-15",
            "geoLocation": "San Francisco Bay, California, USA",
            "projectGoldId": "Gp0127456",
            "_id": "gold_001",
        },
        {
            "biosampleGoldId": "Gb0125342",
            "latitude": 40.7589,
            "longitude": -73.9851,
            "dateCollected": "2017-09-10T11:30:00Z",
            "geographicLocation": "New York Harbor, New York, USA",
            "_id": "gold_002",
        },
        {
            "biosampleGoldId": "Gb0135453",
            "dateCollected": "2018-12-01",
            "description": "Soil sample without GPS coordinates",
            "_id": "gold_003",
        },
    ]


class MockMongoFetcher:
    """Mock MongoDB fetcher for demonstration purposes."""

    def __init__(
        self, adapter_class: type[Any], sample_data: list[dict[str, Any]]
    ) -> None:
        self.adapter = adapter_class()
        self.sample_data = sample_data
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def count_total_samples(self) -> int:
        return len(self.sample_data)

    def count_enrichable_samples(self) -> int:
        count = 0
        for data in self.sample_data:
            try:
                location = self.adapter.extract_location(data)
                if location.is_enrichable():
                    count += 1
            except Exception:
                pass
        return count

    def fetch_enrichable_locations(
        self, limit: int | None = None
    ) -> Iterator[BiosampleLocation]:
        count = 0
        for data in self.sample_data:
            if limit and count >= limit:
                break
            try:
                location = self.adapter.extract_location(data)
                if location.is_enrichable():
                    yield location
                    count += 1
            except Exception:
                pass

    def fetch_locations_by_ids(
        self, ids: list[str], id_field: str = "id"
    ) -> Iterator[BiosampleLocation]:
        for data in self.sample_data:
            if data.get(id_field) in ids:
                yield self.adapter.extract_location(data)

    def fetch_random_locations(self, n: int = 10) -> Iterator[BiosampleLocation]:
        sampled = random.sample(self.sample_data, min(n, len(self.sample_data)))
        for data in sampled:
            yield self.adapter.extract_location(data)

    def fetch_random_enrichable_locations(
        self, n: int = 10
    ) -> Iterator[BiosampleLocation]:
        enrichable = []
        for data in self.sample_data:
            try:
                location = self.adapter.extract_location(data)
                if location.is_enrichable():
                    enrichable.append(location)
            except Exception:
                pass

        sampled = random.sample(enrichable, min(n, len(enrichable)))
        for location in sampled:
            yield location


def demonstrate_unified_adapter() -> dict[str, Any]:
    """Demonstrate unified adapter functionality."""

    # Create mock fetchers
    nmdc_data = get_sample_nmdc_biosamples()
    gold_data = get_sample_gold_biosamples()

    # Set up unified fetcher with mock connections
    unified_fetcher = UnifiedBiosampleFetcher()

    # Use monkey patching to replace the real MongoDB fetchers with mocks

    # Create mock fetchers
    mock_nmdc = MockMongoFetcher(NMDCBiosampleAdapter, nmdc_data)
    mock_gold = MockMongoFetcher(GOLDBiosampleAdapter, gold_data)

    # Replace the fetchers in unified interface
    # Note: This is a demo with mock data, proper typing would require refactoring
    # Using cast to satisfy type checker for mock objects in demo code
    from typing import cast

    unified_fetcher.nmdc_mongo = cast("Any", mock_nmdc)
    unified_fetcher.gold_mongo = cast("Any", mock_gold)

    results = {
        "demonstration_info": {
            "adapter_type": "Unified",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "nmdc_samples": len(nmdc_data),
            "gold_samples": len(gold_data),
            "total_samples": len(nmdc_data) + len(gold_data),
            "description": "Unified biosample adapter demonstration combining NMDC and GOLD sources",
        },
        "source_statistics": {},
        "enrichment_statistics": {},
        "cross_source_analysis": {},
        "sampling_demonstrations": {},
        "id_retrieval_demonstrations": {},
        "unified_interface_tests": {},
    }

    try:
        # Test statistics gathering
        stats = unified_fetcher.get_enrichment_statistics()
        results["source_statistics"] = stats

        # Test enrichable location fetching from all sources
        enrichable_locations = list(
            unified_fetcher.fetch_enrichable_locations(source="all", limit=10)
        )

        # Analyze sources of enrichable locations
        source_breakdown = {"nmdc": 0, "gold": 0}
        for location in enrichable_locations:
            if location.database_source == "NMDC":
                source_breakdown["nmdc"] += 1
            elif location.database_source == "GOLD":
                source_breakdown["gold"] += 1

        results["enrichment_statistics"] = {
            "total_enrichable_found": len(enrichable_locations),
            "source_breakdown": source_breakdown,
            "enrichable_samples": [
                {
                    "sample_id": loc.sample_id,
                    "database_source": loc.database_source,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "collection_date": loc.collection_date,
                    "textual_location": loc.textual_location,
                    "location_completeness": loc.location_completeness,
                }
                for loc in enrichable_locations
            ],
        }

        # Test source-specific fetching
        nmdc_only = list(
            unified_fetcher.fetch_enrichable_locations(source="nmdc", limit=5)
        )
        gold_only = list(
            unified_fetcher.fetch_enrichable_locations(source="gold", limit=5)
        )

        results["cross_source_analysis"] = {
            "nmdc_only_count": len(nmdc_only),
            "gold_only_count": len(gold_only),
            "nmdc_enrichable_rate": len(nmdc_only) / len(nmdc_data) if nmdc_data else 0,
            "gold_enrichable_rate": len(gold_only) / len(gold_data) if gold_data else 0,
            "combined_enrichable_rate": len(enrichable_locations)
            / (len(nmdc_data) + len(gold_data))
            if (nmdc_data or gold_data)
            else 0,
        }

        # Test random sampling
        random_all = list(unified_fetcher.fetch_random_locations(n=4, source="all"))
        random_enrichable = list(
            unified_fetcher.fetch_random_enrichable_locations(n=3, source="all")
        )

        results["sampling_demonstrations"] = {
            "random_sampling": {
                "total_requested": 4,
                "total_received": len(random_all),
                "samples": [
                    {
                        "sample_id": loc.sample_id,
                        "database_source": loc.database_source,
                        "is_enrichable": loc.is_enrichable(),
                    }
                    for loc in random_all
                ],
            },
            "random_enrichable_sampling": {
                "total_requested": 3,
                "total_received": len(random_enrichable),
                "samples": [
                    {
                        "sample_id": loc.sample_id,
                        "database_source": loc.database_source,
                        "is_enrichable": loc.is_enrichable(),
                    }
                    for loc in random_enrichable
                ],
            },
        }

        # Test ID-based retrieval
        nmdc_ids = ["nmdc:bsm-11-34xj1150", "nmdc:bsm-11-45ky2260"]
        gold_ids = ["Gb0115231", "Gb0125342"]

        nmdc_by_id = list(
            unified_fetcher.fetch_locations_by_ids(nmdc_ids, source="nmdc")
        )
        gold_by_id = list(
            unified_fetcher.fetch_locations_by_ids(gold_ids, source="gold")
        )

        results["id_retrieval_demonstrations"] = {
            "nmdc_id_retrieval": {
                "requested_ids": nmdc_ids,
                "found_count": len(nmdc_by_id),
                "found_samples": [
                    {
                        "sample_id": loc.sample_id,
                        "nmdc_biosample_id": loc.nmdc_biosample_id,
                        "is_enrichable": loc.is_enrichable(),
                    }
                    for loc in nmdc_by_id
                ],
            },
            "gold_id_retrieval": {
                "requested_ids": gold_ids,
                "found_count": len(gold_by_id),
                "found_samples": [
                    {
                        "sample_id": loc.sample_id,
                        "gold_biosample_id": loc.gold_biosample_id,
                        "is_enrichable": loc.is_enrichable(),
                    }
                    for loc in gold_by_id
                ],
            },
        }

        # Test unified interface functionality
        results["unified_interface_tests"] = {
            "configuration_test": {
                "nmdc_configured": unified_fetcher.nmdc_mongo is not None,
                "gold_configured": unified_fetcher.gold_mongo is not None,
                "both_sources_available": (
                    unified_fetcher.nmdc_mongo is not None
                    and unified_fetcher.gold_mongo is not None
                ),
            },
            "statistics_aggregation": {
                "aggregates_correctly": "summary" in stats,
                "includes_source_breakdown": "nmdc" in stats and "gold" in stats,
                "calculates_totals": stats.get("summary", {}).get("total_samples", 0)
                > 0,
            },
            "cross_database_functionality": {
                "can_fetch_from_both": len(enrichable_locations) > 0,
                "respects_source_parameter": len(nmdc_only) != len(gold_only)
                or len(nmdc_only) == 0,
                "handles_limits_correctly": len(enrichable_locations) <= 10,
            },
        }

    except Exception as e:
        results["error"] = {
            "message": "Error during unified adapter demonstration",
            "details": str(e),
        }

    return results


@click.command()
@click.option("--output-file", "-o", help="Output file path (default: stdout)")
@click.option("--indent", default=2, help="JSON indentation level", type=int)
def main(output_file: str, indent: int) -> None:
    """Run the unified adapter demonstration and output results as JSON."""
    try:
        results = demonstrate_unified_adapter()
        output = json.dumps(results, indent=indent, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            click.echo(f"Results written to {output_file}")
        else:
            print(output)
    except Exception as e:
        error_result = {
            "error": "Failed to run unified adapter demonstration",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        error_output = json.dumps(error_result, indent=indent)

        if output_file:
            with open(output_file, "w") as f:
                f.write(error_output)
            click.echo(f"Error results written to {output_file}", err=True)
        else:
            print(error_output)
        sys.exit(1)


if __name__ == "__main__":
    main()
