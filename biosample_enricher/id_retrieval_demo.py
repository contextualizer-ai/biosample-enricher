#!/usr/bin/env python3
"""
ID-Based Retrieval Demonstration

Tests ID-based retrieval functionality across different identifier types:
- NMDC biosample ID retrieval
- GOLD biosample ID retrieval
- Alternative identifier lookup
- External database ID resolution
- Cross-reference ID validation
- Performance testing for bulk ID retrieval
"""

import json
import sys
import time
from datetime import datetime
from typing import Any

import click

from biosample_enricher.adapters import (
    GOLDBiosampleAdapter,
    NMDCBiosampleAdapter,
)


def get_sample_nmdc_data_with_ids() -> list[dict[str, Any]]:
    """Get sample NMDC data with various ID types for retrieval testing."""
    return [
        {
            "id": "nmdc:bsm-11-34xj1150",
            "lat_lon": "42.3601 -71.0928",
            "collection_date": {
                "has_raw_value": "2014-11-25",
                "type": "nmdc:TimestampValue",
            },
            "geo_loc_name": {
                "has_raw_value": "Boston Harbor, MA, USA",
                "type": "nmdc:TextValue",
            },
            "associated_studies": ["nmdc:sty-11-34xj1150"],
            "insdc_biosample_identifiers": ["SAMN02728123"],
            "gold_biosample_identifiers": ["gold:Gb0115231"],
            "alternative_identifiers": ["BH_001", "BOSTON_HARBOR_SED_001"],
            "_id": "507f1f77bcf86cd799439011",
        },
        {
            "id": "nmdc:bsm-11-45ky2260",
            "lat_lon": {"latitude": 38.8895, "longitude": -77.0501},
            "collection_date": "2015-06-15T14:30:00Z",
            "geographic_location": "Potomac River, DC, USA",
            "part_of": ["nmdc:sty-11-45ky2260"],
            "ncbi_biosample_identifiers": ["SAMN03456789"],
            "jgi_portal_identifiers": ["502901234"],
            "external_database_identifiers": ["EBI:ERS987654"],
            "_id": "507f1f77bcf86cd799439012",
        },
        {
            "id": "nmdc:bsm-11-56lz3370",
            "lat_lon": [37.7749, -122.4194],
            "collection_date": "2016-08",
            "sample_collection_site": "San Francisco Bay",
            "alternative_identifiers": ["SF_BAY_001", "CALIFORNIA_MARINE_001"],
            "biosample_identifiers": ["SF_SED_CORE_001"],
            "sample_identifiers": ["CA_MARINE_2016_001"],
            "_id": "507f1f77bcf86cd799439013",
        },
        {
            "id": "nmdc:bsm-11-67mn4480",
            "latitude": 40.7589,
            "longitude": -73.9851,
            "collection_date": {
                "has_raw_value": "2017-03",
                "type": "nmdc:TimestampValue",
            },
            "description": {
                "has_raw_value": "NYC harbor sediment",
                "type": "nmdc:TextValue",
            },
            "insdc_biosample_identifiers": ["SAMN04567890"],
            "external_database_identifiers": ["EBI:ERS123456", "DDBJ:DRS789012"],
            "_id": "507f1f77bcf86cd799439014",
        },
    ]


def get_sample_gold_data_with_ids() -> list[dict[str, Any]]:
    """Get sample GOLD data with various ID types for retrieval testing."""
    return [
        {
            "biosampleGoldId": "Gb0115231",
            "latitude": 42.3601,
            "longitude": -71.0928,
            "dateCollected": "2014-11-25",
            "geoLocation": "Boston Harbor, Massachusetts, USA",
            "projectGoldId": "Gp0127456",
            "nmdc_biosample_id": "nmdc:bsm-11-34xj1150",
            "alternative_identifiers": ["GOLD_BH_001"],
            "external_database_identifiers": ["NCBI:SAMN02728123"],
            "_id": "507f1f77bcf86cd799439021",
        },
        {
            "biosampleGoldId": "Gb0125342",
            "latitude": 38.8895,
            "longitude": -77.0501,
            "dateCollected": "2015-06-15T14:30:00Z",
            "geographicLocation": "Potomac River, DC, USA",
            "projectGoldId": "Gp0138567",
            "biosample_identifiers": ["POTOMAC_001"],
            "sample_identifiers": ["DC_RIVER_SED_001"],
            "_id": "507f1f77bcf86cd799439022",
        },
        {
            "biosampleGoldId": "Gb0135453",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "dateCollected": "2016-08",
            "description": "San Francisco Bay sediment",
            "projectGoldId": "Gp0149678",
            "alternative_identifiers": ["SF_GOLD_001", "CALIFORNIA_001"],
            "external_database_identifiers": ["JGI:502901234"],
            "_id": "507f1f77bcf86cd799439023",
        },
        {
            "biosampleGoldId": "Gb0145564",
            "latitude": 33.7490,
            "longitude": -84.3880,
            "dateCollected": "2017",
            "geoLocation": "Atlanta, Georgia, USA",
            "projectGoldId": "Gp0150789",
            "biosample_identifiers": ["ATL_SOIL_001"],
            "external_database_identifiers": ["NCBI:SAMN05678901"],
            "_id": "507f1f77bcf86cd799439024",
        },
    ]


class MockFetcherWithIDs:
    """Mock fetcher that supports ID-based retrieval for demonstration."""

    def __init__(self, adapter_class, sample_data):
        self.adapter = adapter_class()
        self.sample_data = sample_data
        self._connected = False

    def connect(self):
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def fetch_locations_by_ids(self, ids: list[str], id_field: str = "id") -> list:
        """Fetch locations by various ID types."""
        results = []

        for data in self.sample_data:
            location = self.adapter.extract_location(data)
            found_match = False

            # Check primary ID field
            if (
                id_field == "id"
                and data.get("id") in ids
                or id_field == "biosampleGoldId"
                and data.get("biosampleGoldId") in ids
            ):
                found_match = True

            # Check all identifier lists in the location object
            if not found_match:
                all_identifiers = []

                # Collect all identifiers from the location
                if location.alternative_identifiers:
                    all_identifiers.extend(location.alternative_identifiers)
                if location.external_database_identifiers:
                    all_identifiers.extend(location.external_database_identifiers)
                if location.biosample_identifiers:
                    all_identifiers.extend(location.biosample_identifiers)
                if location.sample_identifiers:
                    all_identifiers.extend(location.sample_identifiers)
                if location.nmdc_biosample_id:
                    all_identifiers.append(location.nmdc_biosample_id)
                if location.gold_biosample_id:
                    all_identifiers.append(location.gold_biosample_id)

                # Check if any of the requested IDs match
                if any(req_id in all_identifiers for req_id in ids):
                    found_match = True

            if found_match:
                results.append(location)

        return results

    def fetch_locations_by_alternative_ids(self, ids: list[str]) -> list:
        """Fetch by alternative identifiers."""
        results = []
        for data in self.sample_data:
            location = self.adapter.extract_location(data)
            if location.alternative_identifiers and any(
                alt_id in ids for alt_id in location.alternative_identifiers
            ):
                results.append(location)
        return results

    def fetch_locations_by_external_ids(self, ids: list[str]) -> list:
        """Fetch by external database identifiers."""
        results = []
        for data in self.sample_data:
            location = self.adapter.extract_location(data)
            if location.external_database_identifiers and any(
                ext_id in ids for ext_id in location.external_database_identifiers
            ):
                results.append(location)
        return results


def test_primary_id_retrieval() -> dict[str, Any]:
    """Test retrieval by primary biosample IDs."""
    nmdc_data = get_sample_nmdc_data_with_ids()
    gold_data = get_sample_gold_data_with_ids()

    nmdc_fetcher = MockFetcherWithIDs(NMDCBiosampleAdapter, nmdc_data)
    gold_fetcher = MockFetcherWithIDs(GOLDBiosampleAdapter, gold_data)

    results: dict[str, Any] = {
        "nmdc_primary_id_tests": [],
        "gold_primary_id_tests": [],
        "performance_metrics": {},
    }

    # Test NMDC primary ID retrieval
    nmdc_test_ids = [
        "nmdc:bsm-11-34xj1150",
        "nmdc:bsm-11-45ky2260",
        "nmdc:bsm-nonexistent",
    ]

    start_time = time.time()
    nmdc_results = nmdc_fetcher.fetch_locations_by_ids(nmdc_test_ids, id_field="id")
    nmdc_time = time.time() - start_time

    results["nmdc_primary_id_tests"] = {
        "requested_ids": nmdc_test_ids,
        "found_count": len(nmdc_results),
        "retrieval_time_seconds": round(nmdc_time, 4),
        "found_samples": [
            {
                "sample_id": loc.sample_id,
                "nmdc_biosample_id": loc.nmdc_biosample_id,
                "is_enrichable": loc.is_enrichable(),
            }
            for loc in nmdc_results
        ],
    }

    # Test GOLD primary ID retrieval
    gold_test_ids = ["Gb0115231", "Gb0125342", "Gb0999999"]

    start_time = time.time()
    gold_results = gold_fetcher.fetch_locations_by_ids(
        gold_test_ids, id_field="biosampleGoldId"
    )
    gold_time = time.time() - start_time

    results["gold_primary_id_tests"] = {
        "requested_ids": gold_test_ids,
        "found_count": len(gold_results),
        "retrieval_time_seconds": round(gold_time, 4),
        "found_samples": [
            {
                "sample_id": loc.sample_id,
                "gold_biosample_id": loc.gold_biosample_id,
                "is_enrichable": loc.is_enrichable(),
            }
            for loc in gold_results
        ],
    }

    results["performance_metrics"] = {
        "nmdc_avg_time_per_id": round(nmdc_time / len(nmdc_test_ids), 4),
        "gold_avg_time_per_id": round(gold_time / len(gold_test_ids), 4),
        "total_test_time": round(nmdc_time + gold_time, 4),
    }

    return results


def test_alternative_identifier_retrieval() -> dict[str, Any]:
    """Test retrieval by alternative identifiers."""
    nmdc_data = get_sample_nmdc_data_with_ids()
    gold_data = get_sample_gold_data_with_ids()

    nmdc_fetcher = MockFetcherWithIDs(NMDCBiosampleAdapter, nmdc_data)
    gold_fetcher = MockFetcherWithIDs(GOLDBiosampleAdapter, gold_data)

    results: dict[str, Any] = {
        "alternative_id_tests": {},
        "external_id_tests": {},
        "cross_reference_tests": {},
    }

    # Test alternative identifier retrieval
    alt_test_ids = ["BH_001", "SF_BAY_001", "GOLD_BH_001", "NONEXISTENT_ALT"]

    nmdc_alt_results = nmdc_fetcher.fetch_locations_by_alternative_ids(alt_test_ids)
    gold_alt_results = gold_fetcher.fetch_locations_by_alternative_ids(alt_test_ids)

    results["alternative_id_tests"] = {
        "requested_ids": alt_test_ids,
        "nmdc_found_count": len(nmdc_alt_results),
        "gold_found_count": len(gold_alt_results),
        "nmdc_results": [
            {
                "sample_id": loc.sample_id,
                "matched_alt_ids": [
                    alt_id
                    for alt_id in loc.alternative_identifiers or []
                    if alt_id in alt_test_ids
                ],
            }
            for loc in nmdc_alt_results
        ],
        "gold_results": [
            {
                "sample_id": loc.sample_id,
                "matched_alt_ids": [
                    alt_id
                    for alt_id in loc.alternative_identifiers or []
                    if alt_id in alt_test_ids
                ],
            }
            for loc in gold_alt_results
        ],
    }

    # Test external database identifier retrieval
    ext_test_ids = ["SAMN02728123", "EBI:ERS987654", "JGI:502901234", "NONEXISTENT_EXT"]

    nmdc_ext_results = nmdc_fetcher.fetch_locations_by_external_ids(ext_test_ids)
    gold_ext_results = gold_fetcher.fetch_locations_by_external_ids(ext_test_ids)

    results["external_id_tests"] = {
        "requested_ids": ext_test_ids,
        "nmdc_found_count": len(nmdc_ext_results),
        "gold_found_count": len(gold_ext_results),
        "nmdc_results": [
            {
                "sample_id": loc.sample_id,
                "matched_ext_ids": [
                    ext_id
                    for ext_id in loc.external_database_identifiers or []
                    if ext_id in ext_test_ids
                ],
            }
            for loc in nmdc_ext_results
        ],
        "gold_results": [
            {
                "sample_id": loc.sample_id,
                "matched_ext_ids": [
                    ext_id
                    for ext_id in loc.external_database_identifiers or []
                    if ext_id in ext_test_ids
                ],
            }
            for loc in gold_ext_results
        ],
    }

    # Test cross-reference retrieval (NMDC ID in GOLD data and vice versa)
    cross_ref_results = []

    # Look for NMDC IDs that reference GOLD IDs
    for nmdc_loc in [nmdc_fetcher.adapter.extract_location(data) for data in nmdc_data]:
        if nmdc_loc.gold_biosample_id:
            gold_matches = gold_fetcher.fetch_locations_by_ids(
                [nmdc_loc.gold_biosample_id], id_field="biosampleGoldId"
            )
            if gold_matches:
                cross_ref_results.append(
                    {
                        "nmdc_sample_id": nmdc_loc.sample_id,
                        "references_gold_id": nmdc_loc.gold_biosample_id,
                        "gold_match_found": True,
                        "gold_sample_id": gold_matches[0].sample_id,
                    }
                )

    # Look for GOLD IDs that reference NMDC IDs
    for gold_loc in [gold_fetcher.adapter.extract_location(data) for data in gold_data]:
        if gold_loc.nmdc_biosample_id:
            nmdc_matches = nmdc_fetcher.fetch_locations_by_ids(
                [gold_loc.nmdc_biosample_id], id_field="id"
            )
            if nmdc_matches:
                cross_ref_results.append(
                    {
                        "gold_sample_id": gold_loc.sample_id,
                        "references_nmdc_id": gold_loc.nmdc_biosample_id,
                        "nmdc_match_found": True,
                        "nmdc_sample_id": nmdc_matches[0].sample_id,
                    }
                )

    results["cross_reference_tests"] = {
        "cross_references_found": len(cross_ref_results),
        "cross_reference_details": cross_ref_results,
    }

    return results


def test_bulk_id_retrieval_performance() -> dict[str, Any]:
    """Test performance of bulk ID retrieval operations."""
    nmdc_data = get_sample_nmdc_data_with_ids()
    gold_data = get_sample_gold_data_with_ids()

    nmdc_fetcher = MockFetcherWithIDs(NMDCBiosampleAdapter, nmdc_data)
    gold_fetcher = MockFetcherWithIDs(GOLDBiosampleAdapter, gold_data)

    results: dict[str, Any] = {
        "bulk_retrieval_tests": [],
        "scalability_analysis": {},
        "retrieval_efficiency": {},
    }

    # Test different bulk sizes
    bulk_sizes = [1, 2, 4, 8]

    for bulk_size in bulk_sizes:
        # Generate test IDs
        nmdc_ids = [f"nmdc:bsm-11-{i:08d}" for i in range(bulk_size)]
        gold_ids = [f"Gb{i:07d}" for i in range(bulk_size)]

        # Add some existing IDs to test mixed scenarios
        if bulk_size >= 2:
            nmdc_ids[0] = "nmdc:bsm-11-34xj1150"
            gold_ids[0] = "Gb0115231"

        # Test NMDC bulk retrieval
        start_time = time.time()
        nmdc_bulk_results = nmdc_fetcher.fetch_locations_by_ids(nmdc_ids)
        nmdc_bulk_time = time.time() - start_time

        # Test GOLD bulk retrieval
        start_time = time.time()
        gold_bulk_results = gold_fetcher.fetch_locations_by_ids(
            gold_ids, id_field="biosampleGoldId"
        )
        gold_bulk_time = time.time() - start_time

        bulk_test = {
            "bulk_size": bulk_size,
            "nmdc_test": {
                "requested_ids": nmdc_ids,
                "found_count": len(nmdc_bulk_results),
                "retrieval_time_seconds": round(nmdc_bulk_time, 4),
                "hit_rate": len(nmdc_bulk_results) / len(nmdc_ids),
            },
            "gold_test": {
                "requested_ids": gold_ids,
                "found_count": len(gold_bulk_results),
                "retrieval_time_seconds": round(gold_bulk_time, 4),
                "hit_rate": len(gold_bulk_results) / len(gold_ids),
            },
        }

        bulk_tests = results["bulk_retrieval_tests"]
        if isinstance(bulk_tests, list):
            bulk_tests.append(bulk_test)

    # Analyze scalability
    nmdc_times = [
        test["nmdc_test"]["retrieval_time_seconds"]
        for test in results["bulk_retrieval_tests"]
    ]
    gold_times = [
        test["gold_test"]["retrieval_time_seconds"]
        for test in results["bulk_retrieval_tests"]
    ]

    results["scalability_analysis"] = {
        "nmdc_scalability": {
            "time_complexity": "O(n * m)"
            if len(nmdc_times) > 1
            else "insufficient_data",
            "avg_time_per_id": sum(nmdc_times) / sum(bulk_sizes) if nmdc_times else 0,
            "scaling_factor": nmdc_times[-1] / nmdc_times[0]
            if len(nmdc_times) > 1 and nmdc_times[0] > 0
            else 1,
        },
        "gold_scalability": {
            "time_complexity": "O(n * m)"
            if len(gold_times) > 1
            else "insufficient_data",
            "avg_time_per_id": sum(gold_times) / sum(bulk_sizes) if gold_times else 0,
            "scaling_factor": gold_times[-1] / gold_times[0]
            if len(gold_times) > 1 and gold_times[0] > 0
            else 1,
        },
    }

    # Calculate retrieval efficiency
    total_nmdc_found = sum(
        test["nmdc_test"]["found_count"] for test in results["bulk_retrieval_tests"]
    )
    total_gold_found = sum(
        test["gold_test"]["found_count"] for test in results["bulk_retrieval_tests"]
    )
    total_nmdc_requested = sum(
        len(test["nmdc_test"]["requested_ids"])
        for test in results["bulk_retrieval_tests"]
    )
    total_gold_requested = sum(
        len(test["gold_test"]["requested_ids"])
        for test in results["bulk_retrieval_tests"]
    )

    results["retrieval_efficiency"] = {
        "nmdc_overall_hit_rate": total_nmdc_found / total_nmdc_requested
        if total_nmdc_requested > 0
        else 0,
        "gold_overall_hit_rate": total_gold_found / total_gold_requested
        if total_gold_requested > 0
        else 0,
        "total_samples_found": total_nmdc_found + total_gold_found,
        "total_ids_tested": total_nmdc_requested + total_gold_requested,
    }

    return results


def demonstrate_id_retrieval() -> dict[str, Any]:
    """Demonstrate comprehensive ID-based retrieval functionality."""
    results = {
        "demonstration_info": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "description": "ID-based retrieval demonstration across different identifier types",
            "test_data_summary": {
                "nmdc_samples": len(get_sample_nmdc_data_with_ids()),
                "gold_samples": len(get_sample_gold_data_with_ids()),
                "total_unique_ids_tested": 20,
            },
        },
        "primary_id_retrieval": {},
        "alternative_id_retrieval": {},
        "bulk_retrieval_performance": {},
        "id_type_analysis": {},
        "retrieval_summary": {},
    }

    try:
        # Test primary ID retrieval
        results["primary_id_retrieval"] = test_primary_id_retrieval()

        # Test alternative identifier retrieval
        results["alternative_id_retrieval"] = test_alternative_identifier_retrieval()

        # Test bulk retrieval performance
        results["bulk_retrieval_performance"] = test_bulk_id_retrieval_performance()

        # Analyze ID types and their usage
        nmdc_data = get_sample_nmdc_data_with_ids()
        gold_data = get_sample_gold_data_with_ids()

        nmdc_adapter = NMDCBiosampleAdapter()
        gold_adapter = GOLDBiosampleAdapter()

        id_type_stats: dict[str, Any] = {
            "nmdc_id_types": {},
            "gold_id_types": {},
            "cross_reference_stats": {},
        }

        # Analyze NMDC ID types
        nmdc_id_counts = {
            "has_alternative_identifiers": 0,
            "has_external_database_identifiers": 0,
            "has_biosample_identifiers": 0,
            "has_sample_identifiers": 0,
            "has_gold_biosample_id": 0,
        }

        for data in nmdc_data:
            location = nmdc_adapter.extract_location(data)
            if location.alternative_identifiers:
                nmdc_id_counts["has_alternative_identifiers"] += 1
            if location.external_database_identifiers:
                nmdc_id_counts["has_external_database_identifiers"] += 1
            if location.biosample_identifiers:
                nmdc_id_counts["has_biosample_identifiers"] += 1
            if location.sample_identifiers:
                nmdc_id_counts["has_sample_identifiers"] += 1
            if location.gold_biosample_id:
                nmdc_id_counts["has_gold_biosample_id"] += 1

        id_type_stats["nmdc_id_types"] = nmdc_id_counts

        # Analyze GOLD ID types
        gold_id_counts = {
            "has_alternative_identifiers": 0,
            "has_external_database_identifiers": 0,
            "has_biosample_identifiers": 0,
            "has_sample_identifiers": 0,
            "has_nmdc_biosample_id": 0,
        }

        for data in gold_data:
            location = gold_adapter.extract_location(data)
            if location.alternative_identifiers:
                gold_id_counts["has_alternative_identifiers"] += 1
            if location.external_database_identifiers:
                gold_id_counts["has_external_database_identifiers"] += 1
            if location.biosample_identifiers:
                gold_id_counts["has_biosample_identifiers"] += 1
            if location.sample_identifiers:
                gold_id_counts["has_sample_identifiers"] += 1
            if location.nmdc_biosample_id:
                gold_id_counts["has_nmdc_biosample_id"] += 1

        id_type_stats["gold_id_types"] = gold_id_counts

        # Cross-reference statistics
        alt_id_results = results["alternative_id_retrieval"]
        cross_ref_count = 0
        if isinstance(alt_id_results, dict):
            cross_ref_tests = alt_id_results.get("cross_reference_tests", {})
            if isinstance(cross_ref_tests, dict):
                cross_ref_count = cross_ref_tests.get("cross_references_found", 0)

        id_type_stats["cross_reference_stats"] = {
            "nmdc_samples_with_gold_refs": nmdc_id_counts["has_gold_biosample_id"],
            "gold_samples_with_nmdc_refs": gold_id_counts["has_nmdc_biosample_id"],
            "bidirectional_links": cross_ref_count,
        }

        results["id_type_analysis"] = id_type_stats

        # Generate retrieval summary
        primary_tests = results.get("primary_id_retrieval", {})
        alt_tests = results.get("alternative_id_retrieval", {})
        bulk_tests = results.get("bulk_retrieval_performance", {})

        # Safe retrieval summary with type checking
        summary: dict[str, Any] = {
            "total_retrieval_tests": 3,
        }

        # Primary ID success rates with safe access
        if isinstance(primary_tests, dict):
            nmdc_primary = primary_tests.get("nmdc_primary_id_tests", {})
            gold_primary = primary_tests.get("gold_primary_id_tests", {})
            if isinstance(nmdc_primary, dict) and isinstance(gold_primary, dict):
                nmdc_found = nmdc_primary.get("found_count", 0)
                nmdc_requested = nmdc_primary.get("requested_ids", [])
                gold_found = gold_primary.get("found_count", 0)
                gold_requested = gold_primary.get("requested_ids", [])

                summary["primary_id_success_rate"] = {
                    "nmdc": nmdc_found / len(nmdc_requested) if nmdc_requested else 0,
                    "gold": gold_found / len(gold_requested) if gold_requested else 0,
                }

        # Alternative ID effectiveness with safe access
        if isinstance(alt_tests, dict):
            alt_id_tests = alt_tests.get("alternative_id_tests", {})
            ext_id_tests = alt_tests.get("external_id_tests", {})
            cross_ref_tests = alt_tests.get("cross_reference_tests", {})

            summary["alternative_id_effectiveness"] = {
                "alternative_ids_tested": len(alt_id_tests.get("requested_ids", []))
                if isinstance(alt_id_tests, dict)
                else 0,
                "external_ids_tested": len(ext_id_tests.get("requested_ids", []))
                if isinstance(ext_id_tests, dict)
                else 0,
                "cross_references_found": cross_ref_tests.get(
                    "cross_references_found", 0
                )
                if isinstance(cross_ref_tests, dict)
                else 0,
            }

        # Bulk retrieval performance with safe access
        if isinstance(bulk_tests, dict):
            bulk_retrieval_tests = bulk_tests.get("bulk_retrieval_tests", [])
            retrieval_efficiency = bulk_tests.get("retrieval_efficiency", {})

            largest_bulk = 0
            if isinstance(bulk_retrieval_tests, list) and bulk_retrieval_tests:
                try:
                    largest_bulk = max(
                        test.get("bulk_size", 0)
                        for test in bulk_retrieval_tests
                        if isinstance(test, dict)
                    )
                except (ValueError, TypeError):
                    largest_bulk = 0

            overall_hit_rate = 0.0
            if isinstance(retrieval_efficiency, dict):
                total_found = retrieval_efficiency.get("total_samples_found", 0)
                total_tested = retrieval_efficiency.get("total_ids_tested", 1)
                overall_hit_rate = total_found / total_tested if total_tested > 0 else 0

            summary["bulk_retrieval_performance"] = {
                "largest_bulk_size_tested": largest_bulk,
                "overall_hit_rate": overall_hit_rate,
            }

        # ID coverage analysis
        summary["id_coverage_analysis"] = {
            "nmdc_samples_with_multiple_id_types": sum(
                1 for count in nmdc_id_counts.values() if count > 0
            ),
            "gold_samples_with_multiple_id_types": sum(
                1 for count in gold_id_counts.values() if count > 0
            ),
        }

        results["retrieval_summary"] = summary

    except Exception as e:
        results["error"] = {
            "message": "Error during ID retrieval demonstration",
            "details": str(e),
        }

    return results


@click.command()
@click.option("--output-file", "-o", help="Output file path (default: stdout)")
@click.option("--indent", default=2, help="JSON indentation level", type=int)
def main(output_file: str, indent: int):
    """Run the ID retrieval demonstration and output results as JSON."""
    try:
        results = demonstrate_id_retrieval()
        output = json.dumps(results, indent=indent, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            click.echo(f"Results written to {output_file}")
        else:
            print(output)
    except Exception as e:
        error_result = {
            "error": "Failed to run ID retrieval demonstration",
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
