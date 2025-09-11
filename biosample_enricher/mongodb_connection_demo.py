#!/usr/bin/env python3
"""
MongoDB Connection Demonstration

Tests actual MongoDB connectivity and fetcher functionality:
- MongoDB connection establishment and authentication
- Real database querying and sampling
- Connection error handling and recovery
- Performance metrics for different query types
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import click
import pymongo

from biosample_enricher.adapters import (
    MongoGOLDBiosampleFetcher,
    MongoNMDCBiosampleFetcher,
    UnifiedBiosampleFetcher,
)


def get_mongo_connection_string(mongo_uri: str | None = None) -> str:
    """Get MongoDB connection string from parameter, environment, or default."""
    if mongo_uri:
        return mongo_uri
    return os.getenv(
        "MONGO_URI",
        "mongodb://ncbi_reader:register_manatee_coach78@localhost:27778/?directConnection=true&authMechanism=DEFAULT&authSource=admin",
    )


def test_mongodb_connection(connection_string: str) -> dict[str, Any]:
    """Test basic MongoDB connection."""
    try:
        start_time = time.time()
        client: pymongo.MongoClient = pymongo.MongoClient(connection_string)

        # Test connection by listing databases
        db_names = client.list_database_names()
        connection_time = time.time() - start_time

        client.close()

        return {
            "success": True,
            "connection_time_seconds": round(connection_time, 3),
            "available_databases": db_names,
            "connection_string_format": "authenticated_uri"
            if "@" in connection_string
            else "simple_uri",
        }

    except Exception as e:
        return {"success": False, "error": "connection_failed", "details": str(e)}


def test_nmdc_fetcher(connection_string: str) -> dict[str, Any]:
    """Test NMDC MongoDB fetcher functionality."""
    fetcher = MongoNMDCBiosampleFetcher(
        connection_string=connection_string,
        database_name="nmdc",
        collection_name="biosample_set",
    )

    result = {
        "fetcher_type": "NMDC",
        "database": "nmdc",
        "collection": "biosample_set",
        "connection_test": {},
        "count_tests": {},
        "sampling_tests": {},
        "query_performance": {},
    }

    try:
        # Test connection
        start_time = time.time()
        connection_success = fetcher.connect()
        connection_time = time.time() - start_time

        result["connection_test"] = {
            "success": connection_success,
            "connection_time_seconds": round(connection_time, 3),
        }

        if connection_success:
            # Test counting
            start_time = time.time()
            total_count = fetcher.count_total_samples()
            count_time = time.time() - start_time

            start_time = time.time()
            enrichable_count = fetcher.count_enrichable_samples()
            enrichable_count_time = time.time() - start_time

            result["count_tests"] = {
                "total_samples": total_count,
                "enrichable_samples": enrichable_count,
                "enrichable_rate": enrichable_count / total_count
                if total_count > 0
                else 0.0,
                "total_count_time_seconds": round(count_time, 3),
                "enrichable_count_time_seconds": round(enrichable_count_time, 3),
            }

            # Test sampling
            if total_count > 0:
                start_time = time.time()
                random_sample = list(fetcher.fetch_random_locations(n=3))
                random_time = time.time() - start_time

                start_time = time.time()
                enrichable_sample = list(fetcher.fetch_enrichable_locations(limit=3))
                enrichable_time = time.time() - start_time

                result["sampling_tests"] = {
                    "random_sample_count": len(random_sample),
                    "enrichable_sample_count": len(enrichable_sample),
                    "random_sampling_time_seconds": round(random_time, 3),
                    "enrichable_sampling_time_seconds": round(enrichable_time, 3),
                    "sample_data": [
                        {
                            "sample_id": loc.sample_id,
                            "database_source": loc.database_source,
                            "is_enrichable": loc.is_enrichable(),
                            "location_completeness": loc.location_completeness,
                        }
                        for loc in random_sample[:2]  # Just first 2 for brevity
                    ],
                }

                # Test ID-based retrieval if we have samples
                if random_sample:
                    test_ids = [
                        loc.sample_id for loc in random_sample[:2] if loc.sample_id
                    ]
                    if test_ids:
                        start_time = time.time()
                        id_retrieved = list(fetcher.fetch_locations_by_ids(test_ids))
                        id_time = time.time() - start_time

                        result["query_performance"] = {
                            "id_retrieval_test": {
                                "requested_ids": len(test_ids),
                                "found_samples": len(id_retrieved),
                                "retrieval_time_seconds": round(id_time, 3),
                            }
                        }

        fetcher.disconnect()

    except Exception as e:
        error_info = {"message": "NMDC fetcher test failed", "details": str(e)}
        try:
            fetcher.disconnect()
        except Exception as disconnect_error:
            # Log disconnect error but don't override main error
            error_info["disconnect_error"] = str(disconnect_error)
        result["error"] = error_info

    return result


def test_gold_fetcher(connection_string: str) -> dict[str, Any]:
    """Test GOLD MongoDB fetcher functionality."""
    fetcher = MongoGOLDBiosampleFetcher(
        connection_string=connection_string,
        database_name="gold_metadata",
        collection_name="biosamples",
    )

    result = {
        "fetcher_type": "GOLD",
        "database": "gold_metadata",
        "collection": "biosamples",
        "connection_test": {},
        "count_tests": {},
        "sampling_tests": {},
        "query_performance": {},
    }

    try:
        # Test connection
        start_time = time.time()
        connection_success = fetcher.connect()
        connection_time = time.time() - start_time

        result["connection_test"] = {
            "success": connection_success,
            "connection_time_seconds": round(connection_time, 3),
        }

        if connection_success:
            # Test counting
            start_time = time.time()
            total_count = fetcher.count_total_samples()
            count_time = time.time() - start_time

            start_time = time.time()
            enrichable_count = fetcher.count_enrichable_samples()
            enrichable_count_time = time.time() - start_time

            result["count_tests"] = {
                "total_samples": total_count,
                "enrichable_samples": enrichable_count,
                "enrichable_rate": enrichable_count / total_count
                if total_count > 0
                else 0.0,
                "total_count_time_seconds": round(count_time, 3),
                "enrichable_count_time_seconds": round(enrichable_count_time, 3),
            }

            # Test sampling
            if total_count > 0:
                start_time = time.time()
                random_sample = list(fetcher.fetch_random_locations(n=3))
                random_time = time.time() - start_time

                start_time = time.time()
                enrichable_sample = list(fetcher.fetch_enrichable_locations(limit=3))
                enrichable_time = time.time() - start_time

                result["sampling_tests"] = {
                    "random_sample_count": len(random_sample),
                    "enrichable_sample_count": len(enrichable_sample),
                    "random_sampling_time_seconds": round(random_time, 3),
                    "enrichable_sampling_time_seconds": round(enrichable_time, 3),
                    "sample_data": [
                        {
                            "sample_id": loc.sample_id,
                            "database_source": loc.database_source,
                            "is_enrichable": loc.is_enrichable(),
                            "location_completeness": loc.location_completeness,
                            "gold_biosample_id": loc.gold_biosample_id,
                        }
                        for loc in random_sample[:2]  # Just first 2 for brevity
                    ],
                }

                # Test ID-based retrieval using GOLD IDs
                if random_sample:
                    test_ids = [
                        loc.gold_biosample_id
                        for loc in random_sample[:2]
                        if loc.gold_biosample_id
                    ]
                    if test_ids:
                        start_time = time.time()
                        id_retrieved = list(
                            fetcher.fetch_locations_by_ids(
                                test_ids, id_field="biosampleGoldId"
                            )
                        )
                        id_time = time.time() - start_time

                        result["query_performance"] = {
                            "id_retrieval_test": {
                                "requested_ids": len(test_ids),
                                "found_samples": len(id_retrieved),
                                "retrieval_time_seconds": round(id_time, 3),
                                "id_field_used": "biosampleGoldId",
                            }
                        }

        fetcher.disconnect()

    except Exception as e:
        error_info = {"message": "GOLD fetcher test failed", "details": str(e)}
        try:
            fetcher.disconnect()
        except Exception as disconnect_error:
            # Log disconnect error but don't override main error
            error_info["disconnect_error"] = str(disconnect_error)
        result["error"] = error_info

    return result


def test_unified_fetcher(connection_string: str) -> dict[str, Any]:
    """Test unified fetcher with real MongoDB connections."""
    unified = UnifiedBiosampleFetcher()

    # Configure both sources
    unified.configure_nmdc_mongo(connection_string, "nmdc", "biosample_set")
    unified.configure_gold_mongo(connection_string, "gold_metadata", "biosamples")

    result = {
        "fetcher_type": "Unified",
        "configuration": {
            "nmdc_configured": unified.nmdc_mongo is not None,
            "gold_configured": unified.gold_mongo is not None,
        },
        "statistics_test": {},
        "cross_source_sampling": {},
        "performance_comparison": {},
    }

    try:
        # Test statistics gathering
        start_time = time.time()
        stats = unified.get_enrichment_statistics()
        stats_time = time.time() - start_time

        result["statistics_test"] = {
            "statistics_time_seconds": round(stats_time, 3),
            "statistics_data": stats,
        }

        # Test cross-source sampling
        start_time = time.time()
        combined_sample = list(
            unified.fetch_enrichable_locations(source="all", limit=5)
        )
        combined_time = time.time() - start_time

        start_time = time.time()
        nmdc_sample = list(unified.fetch_enrichable_locations(source="nmdc", limit=3))
        nmdc_time = time.time() - start_time

        start_time = time.time()
        gold_sample = list(unified.fetch_enrichable_locations(source="gold", limit=3))
        gold_time = time.time() - start_time

        result["cross_source_sampling"] = {
            "combined_sample_count": len(combined_sample),
            "nmdc_sample_count": len(nmdc_sample),
            "gold_sample_count": len(gold_sample),
            "combined_sampling_time_seconds": round(combined_time, 3),
            "nmdc_sampling_time_seconds": round(nmdc_time, 3),
            "gold_sampling_time_seconds": round(gold_time, 3),
            "source_distribution": {
                "nmdc_in_combined": sum(
                    1 for loc in combined_sample if loc.database_source == "NMDC"
                ),
                "gold_in_combined": sum(
                    1 for loc in combined_sample if loc.database_source == "GOLD"
                ),
            },
        }

        # Performance comparison
        total_samples = stats.get("summary", {}).get("total_samples", 0)
        total_enrichable = stats.get("summary", {}).get("total_enrichable_samples", 0)

        result["performance_comparison"] = {
            "database_scale": {
                "total_samples_available": total_samples,
                "total_enrichable_available": total_enrichable,
                "sample_to_result_ratio": len(combined_sample) / total_enrichable
                if total_enrichable > 0
                else 0,
            },
            "query_efficiency": {
                "avg_time_per_sample": round(combined_time / len(combined_sample), 4)
                if combined_sample
                else 0,
                "samples_per_second": round(len(combined_sample) / combined_time, 2)
                if combined_time > 0
                else 0,
            },
        }

    except Exception as e:
        result["error"] = {"message": "Unified fetcher test failed", "details": str(e)}

    return result


def demonstrate_mongodb_connection(
    connection_string: str, _nmdc_db: str = "nmdc", _gold_db: str = "gold_metadata"
) -> dict[str, Any]:
    """Demonstrate MongoDB connection and fetcher functionality."""

    results: dict[str, Any] = {
        "demonstration_info": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "connection_string_source": "environment"
            if "MONGO_URI" in os.environ
            else "default",
            "description": "MongoDB connection and fetcher functionality demonstration",
        },
        "basic_connection_test": {},
        "nmdc_fetcher_test": {},
        "gold_fetcher_test": {},
        "unified_fetcher_test": {},
        "overall_assessment": {},
    }

    # Test basic connection
    results["basic_connection_test"] = test_mongodb_connection(connection_string)

    # Test individual fetchers
    if results["basic_connection_test"].get("success"):
        results["nmdc_fetcher_test"] = test_nmdc_fetcher(connection_string)
        results["gold_fetcher_test"] = test_gold_fetcher(connection_string)
        results["unified_fetcher_test"] = test_unified_fetcher(connection_string)
    else:
        results["nmdc_fetcher_test"] = {"skipped": "basic connection failed"}
        results["gold_fetcher_test"] = {"skipped": "basic connection failed"}
        results["unified_fetcher_test"] = {"skipped": "basic connection failed"}

    # Overall assessment
    nmdc_success = "error" not in results["nmdc_fetcher_test"]
    gold_success = "error" not in results["gold_fetcher_test"]
    unified_success = "error" not in results["unified_fetcher_test"]

    results["overall_assessment"] = {
        "basic_connection_works": results["basic_connection_test"].get(
            "success", False
        ),
        "nmdc_fetcher_works": nmdc_success,
        "gold_fetcher_works": gold_success,
        "unified_fetcher_works": unified_success,
        "all_systems_operational": all(
            [
                results["basic_connection_test"].get("success", False),
                nmdc_success,
                gold_success,
                unified_success,
            ]
        ),
        "available_databases": results.get("basic_connection_test", {}).get(
            "available_databases", []
        )
        if isinstance(results.get("basic_connection_test"), dict)
        else [],
        "performance_summary": _get_performance_summary(results),
    }

    return results


def _get_performance_summary(results: dict[str, Any]) -> dict[str, Any]:
    """Safely extract performance summary from results."""
    nmdc_total = 0
    gold_total = 0
    combined_rate = 0.0

    # Safe access for NMDC total samples
    nmdc_test = results.get("nmdc_fetcher_test", {})
    if isinstance(nmdc_test, dict):
        count_tests = nmdc_test.get("count_tests", {})
        if isinstance(count_tests, dict):
            nmdc_total = count_tests.get("total_samples", 0)

    # Safe access for GOLD total samples
    gold_test = results.get("gold_fetcher_test", {})
    if isinstance(gold_test, dict):
        count_tests = gold_test.get("count_tests", {})
        if isinstance(count_tests, dict):
            gold_total = count_tests.get("total_samples", 0)

    # Safe access for combined enrichable rate
    unified_test = results.get("unified_fetcher_test", {})
    if isinstance(unified_test, dict):
        stats_test = unified_test.get("statistics_test", {})
        if isinstance(stats_test, dict):
            stats_data = stats_test.get("statistics_data", {})
            if isinstance(stats_data, dict):
                summary = stats_data.get("summary", {})
                if isinstance(summary, dict):
                    combined_rate = summary.get("enrichable_coverage", 0.0)

    return {
        "nmdc_total_samples": nmdc_total,
        "gold_total_samples": gold_total,
        "combined_enrichable_rate": combined_rate,
    }


@click.command()
@click.option("--output-file", "-o", help="Output file path (default: stdout)")
@click.option("--indent", default=2, help="JSON indentation level", type=int)
@click.option(
    "--mongo-uri", help="MongoDB connection URI (default: environment or hardcoded)"
)
@click.option("--nmdc-db", default="nmdc", help="NMDC database name")
@click.option("--gold-db", default="gold_metadata", help="GOLD database name")
def main(
    output_file: str, indent: int, mongo_uri: str, nmdc_db: str, gold_db: str
) -> None:
    """Run the MongoDB connection demonstration and output results as JSON."""
    try:
        connection_string = get_mongo_connection_string(mongo_uri)
        results = demonstrate_mongodb_connection(connection_string, nmdc_db, gold_db)
        output = json.dumps(results, indent=indent, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            click.echo(f"Results written to {output_file}")
        else:
            print(output)
    except Exception as e:
        error_result = {
            "error": "Failed to run MongoDB connection demonstration",
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
