#!/usr/bin/env python3
"""
Random Sampling Demonstration

Tests MongoDB aggregation pipeline for efficient random sampling:
- MongoDB $sample aggregation for truly random sampling
- Performance comparison vs scanning and filtering
- Random enrichable sample selection
- Sampling bias analysis
- Large dataset random sampling efficiency
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import click

from biosample_enricher.adapters import (
    MongoGOLDBiosampleFetcher,
    MongoNMDCBiosampleFetcher,
    UnifiedBiosampleFetcher,
)


def get_mongo_connection_string(mongo_uri: str | None = None) -> str:
    """Get MongoDB connection string from environment or default."""
    if mongo_uri:
        return mongo_uri
    return os.getenv(
        "MONGO_URI",
        "mongodb://ncbi_reader:register_manatee_coach78@localhost:27778/?directConnection=true&authMechanism=DEFAULT&authSource=admin",
    )


def test_mongodb_random_sampling() -> dict[str, Any]:
    """Test MongoDB aggregation pipeline random sampling vs sequential sampling."""
    connection_string = get_mongo_connection_string()

    # Test NMDC random sampling
    nmdc_fetcher = MongoNMDCBiosampleFetcher(
        connection_string=connection_string,
        database_name="nmdc",
        collection_name="biosample_set",
    )

    # Test GOLD random sampling
    gold_fetcher = MongoGOLDBiosampleFetcher(
        connection_string=connection_string,
        database_name="gold_metadata",
        collection_name="biosamples",
    )

    results: dict[str, Any] = {
        "nmdc_sampling_tests": {},
        "gold_sampling_tests": {},
        "sampling_comparison": {},
        "performance_analysis": {},
    }

    try:
        # Test NMDC sampling
        if nmdc_fetcher.connect():
            nmdc_results = _test_fetcher_sampling(nmdc_fetcher, "NMDC")
            results["nmdc_sampling_tests"] = nmdc_results
            nmdc_fetcher.disconnect()
        else:
            results["nmdc_sampling_tests"] = {
                "error": "Failed to connect to NMDC MongoDB"
            }

        # Test GOLD sampling
        if gold_fetcher.connect():
            gold_results = _test_fetcher_sampling(gold_fetcher, "GOLD")
            results["gold_sampling_tests"] = gold_results
            gold_fetcher.disconnect()
        else:
            results["gold_sampling_tests"] = {
                "error": "Failed to connect to GOLD MongoDB"
            }

        # Compare sampling methods
        if (
            "error" not in results["nmdc_sampling_tests"]
            and "error" not in results["gold_sampling_tests"]
        ):
            results["sampling_comparison"] = _compare_sampling_methods(
                results["nmdc_sampling_tests"], results["gold_sampling_tests"]
            )

        # Performance analysis
        results["performance_analysis"] = _analyze_sampling_performance(results)

    except Exception as e:
        results["error"] = {
            "message": "Error during random sampling test",
            "details": str(e),
        }

    return results


def _test_fetcher_sampling(fetcher: Any, source_name: str) -> dict[str, Any]:
    """Test sampling methods for a specific fetcher."""
    results: dict[str, Any] = {
        "source": source_name,
        "total_sample_count": 0,
        "enrichable_sample_count": 0,
        "random_sampling_tests": [],
        "enrichable_sampling_tests": [],
        "aggregation_pipeline_tests": [],
    }

    try:
        # Get basic counts
        results["total_sample_count"] = fetcher.count_total_samples()
        results["enrichable_sample_count"] = fetcher.count_enrichable_samples()

        if results["total_sample_count"] == 0:
            results["note"] = "No samples available for testing"
            return results

        # Test different random sampling sizes
        sample_sizes = [5, 10, 25, 50]
        for sample_size in sample_sizes:
            if sample_size <= int(results["total_sample_count"]):
                # Test random sampling
                start_time = time.time()
                random_samples = list(fetcher.fetch_random_locations(n=sample_size))
                random_time = time.time() - start_time

                # Analyze sample distribution
                enrichable_in_random = sum(
                    1 for loc in random_samples if loc.is_enrichable()
                )

                sample_test = {
                    "sample_size_requested": sample_size,
                    "samples_returned": len(random_samples),
                    "sampling_time_seconds": round(random_time, 4),
                    "enrichable_in_sample": enrichable_in_random,
                    "enrichable_rate_in_sample": enrichable_in_random
                    / len(random_samples)
                    if random_samples
                    else 0,
                    "avg_time_per_sample": round(random_time / len(random_samples), 6)
                    if random_samples
                    else 0,
                    "sample_coordinates": [
                        {
                            "sample_id": loc.sample_id,
                            "latitude": loc.latitude,
                            "longitude": loc.longitude,
                            "is_enrichable": loc.is_enrichable(),
                        }
                        for loc in random_samples[:3]  # First 3 for analysis
                    ],
                }

                results["random_sampling_tests"].append(sample_test)

        # Test enrichable-only sampling
        enrichable_sample_sizes = [3, 5, 10, 20]
        for sample_size in enrichable_sample_sizes:
            if sample_size <= results["enrichable_sample_count"]:
                # Test enrichable sampling
                start_time = time.time()
                enrichable_samples = list(
                    fetcher.fetch_enrichable_locations(limit=sample_size)
                )
                enrichable_time = time.time() - start_time

                enrichable_test = {
                    "sample_size_requested": sample_size,
                    "samples_returned": len(enrichable_samples),
                    "sampling_time_seconds": round(enrichable_time, 4),
                    "all_enrichable_verified": all(
                        loc.is_enrichable() for loc in enrichable_samples
                    ),
                    "avg_time_per_sample": round(
                        enrichable_time / len(enrichable_samples), 6
                    )
                    if enrichable_samples
                    else 0,
                    "completeness_distribution": [
                        round(loc.location_completeness, 3)
                        for loc in enrichable_samples[:5]
                    ],
                }

                results["enrichable_sampling_tests"].append(enrichable_test)

        # Test MongoDB aggregation pipeline efficiency
        if hasattr(fetcher, "fetch_random_enrichable_locations"):
            pipeline_sizes = [5, 15, 30]
            for size in pipeline_sizes:
                if size <= results["enrichable_sample_count"]:
                    start_time = time.time()
                    pipeline_samples = list(
                        fetcher.fetch_random_enrichable_locations(n=size)
                    )
                    pipeline_time = time.time() - start_time

                    pipeline_test = {
                        "sample_size_requested": size,
                        "samples_returned": len(pipeline_samples),
                        "sampling_time_seconds": round(pipeline_time, 4),
                        "all_enrichable_verified": all(
                            loc.is_enrichable() for loc in pipeline_samples
                        ),
                        "pipeline_efficiency": round(
                            len(pipeline_samples) / pipeline_time, 2
                        )
                        if pipeline_time > 0
                        else 0,
                        "method": "mongodb_aggregation_pipeline",
                    }

                    results["aggregation_pipeline_tests"].append(pipeline_test)

    except Exception as e:
        results["error"] = {
            "message": f"Error testing {source_name} sampling",
            "details": str(e),
        }

    return results


def _compare_sampling_methods(
    nmdc_results: dict[str, Any], gold_results: dict[str, Any]
) -> dict[str, Any]:
    """Compare sampling methods between NMDC and GOLD."""
    comparison: dict[str, Any] = {
        "dataset_scale_comparison": {},
        "sampling_efficiency_comparison": {},
        "enrichable_rate_comparison": {},
        "method_performance_comparison": {},
    }

    # Dataset scale comparison
    comparison["dataset_scale_comparison"] = {
        "nmdc_total_samples": nmdc_results.get("total_sample_count", 0),
        "gold_total_samples": gold_results.get("total_sample_count", 0),
        "nmdc_enrichable_samples": nmdc_results.get("enrichable_sample_count", 0),
        "gold_enrichable_samples": gold_results.get("enrichable_sample_count", 0),
        "nmdc_enrichable_rate": (
            nmdc_results.get("enrichable_sample_count", 0)
            / nmdc_results.get("total_sample_count", 1)
            if nmdc_results.get("total_sample_count", 0) > 0
            else 0
        ),
        "gold_enrichable_rate": (
            gold_results.get("enrichable_sample_count", 0)
            / gold_results.get("total_sample_count", 1)
            if gold_results.get("total_sample_count", 0) > 0
            else 0
        ),
    }

    # Sampling efficiency comparison
    nmdc_random_tests = nmdc_results.get("random_sampling_tests", [])
    gold_random_tests = gold_results.get("random_sampling_tests", [])

    if nmdc_random_tests and gold_random_tests:
        nmdc_avg_time = sum(
            test["avg_time_per_sample"] for test in nmdc_random_tests
        ) / len(nmdc_random_tests)
        gold_avg_time = sum(
            test["avg_time_per_sample"] for test in gold_random_tests
        ) / len(gold_random_tests)

        comparison["sampling_efficiency_comparison"] = {
            "nmdc_avg_time_per_sample": round(nmdc_avg_time, 6),
            "gold_avg_time_per_sample": round(gold_avg_time, 6),
            "faster_source": "NMDC" if nmdc_avg_time < gold_avg_time else "GOLD",
            "speed_difference_factor": round(
                max(nmdc_avg_time, gold_avg_time) / min(nmdc_avg_time, gold_avg_time), 2
            ),
        }

    # Enrichment rate in samples comparison
    nmdc_sample_rates = [
        test["enrichable_rate_in_sample"] for test in nmdc_random_tests
    ]
    gold_sample_rates = [
        test["enrichable_rate_in_sample"] for test in gold_random_tests
    ]

    if nmdc_sample_rates and gold_sample_rates:
        comparison["enrichable_rate_comparison"] = {
            "nmdc_avg_enrichment_in_random_samples": round(
                sum(nmdc_sample_rates) / len(nmdc_sample_rates), 3
            ),
            "gold_avg_enrichment_in_random_samples": round(
                sum(gold_sample_rates) / len(gold_sample_rates), 3
            ),
            "nmdc_enrichment_variance": round(
                _calculate_variance(nmdc_sample_rates), 4
            ),
            "gold_enrichment_variance": round(
                _calculate_variance(gold_sample_rates), 4
            ),
        }

    # Method performance comparison
    nmdc_pipeline_tests = nmdc_results.get("aggregation_pipeline_tests", [])
    gold_pipeline_tests = gold_results.get("aggregation_pipeline_tests", [])

    comparison["method_performance_comparison"] = {
        "aggregation_pipeline_available": {
            "nmdc": len(nmdc_pipeline_tests) > 0,
            "gold": len(gold_pipeline_tests) > 0,
        }
    }

    if nmdc_pipeline_tests and gold_pipeline_tests:
        nmdc_pipeline_efficiency = sum(
            test["pipeline_efficiency"] for test in nmdc_pipeline_tests
        ) / len(nmdc_pipeline_tests)
        gold_pipeline_efficiency = sum(
            test["pipeline_efficiency"] for test in gold_pipeline_tests
        ) / len(gold_pipeline_tests)

        comparison["method_performance_comparison"]["pipeline_efficiency"] = {
            "nmdc_samples_per_second": round(nmdc_pipeline_efficiency, 2),
            "gold_samples_per_second": round(gold_pipeline_efficiency, 2),
            "more_efficient_source": "NMDC"
            if nmdc_pipeline_efficiency > gold_pipeline_efficiency
            else "GOLD",
        }

    return comparison


def _calculate_variance(values: list[float]) -> float:
    """Calculate variance of a list of values."""
    if not values:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance


def _analyze_sampling_performance(results: dict[str, Any]) -> dict[str, Any]:
    """Analyze overall sampling performance and provide recommendations."""
    analysis: dict[str, Any] = {
        "performance_summary": {},
        "sampling_recommendations": {},
        "scalability_assessment": {},
    }

    nmdc_tests = results.get("nmdc_sampling_tests", {})
    gold_tests = results.get("gold_sampling_tests", {})

    # Performance summary
    total_tests = 0
    total_samples = 0
    total_time = 0

    for test_type in [
        "random_sampling_tests",
        "enrichable_sampling_tests",
        "aggregation_pipeline_tests",
    ]:
        for source_tests in [nmdc_tests, gold_tests]:
            if test_type in source_tests:
                for test in source_tests[test_type]:
                    total_tests += 1
                    total_samples += test.get("samples_returned", 0)
                    total_time += test.get("sampling_time_seconds", 0)

    analysis["performance_summary"] = {
        "total_sampling_tests": total_tests,
        "total_samples_retrieved": total_samples,
        "total_time_spent": round(total_time, 3),
        "overall_samples_per_second": round(total_samples / total_time, 2)
        if total_time > 0
        else 0,
    }

    # Sampling recommendations
    recommendations: list[str] = []

    # Check if MongoDB aggregation is available and efficient
    nmdc_pipeline = nmdc_tests.get("aggregation_pipeline_tests", [])
    gold_pipeline = gold_tests.get("aggregation_pipeline_tests", [])

    if nmdc_pipeline or gold_pipeline:
        recommendations.append(
            "Use MongoDB aggregation pipeline for random sampling when available"
        )

        if nmdc_pipeline and gold_pipeline:
            nmdc_efficiency = sum(
                test["pipeline_efficiency"] for test in nmdc_pipeline
            ) / len(nmdc_pipeline)
            gold_efficiency = sum(
                test["pipeline_efficiency"] for test in gold_pipeline
            ) / len(gold_pipeline)

            if nmdc_efficiency > gold_efficiency * 1.5:
                recommendations.append(
                    "NMDC sampling is significantly more efficient than GOLD"
                )
            elif gold_efficiency > nmdc_efficiency * 1.5:
                recommendations.append(
                    "GOLD sampling is significantly more efficient than NMDC"
                )

    # Check enrichment rates
    comparison = results.get("sampling_comparison", {})
    enrichment_comparison = comparison.get("enrichable_rate_comparison", {})

    if enrichment_comparison:
        nmdc_rate = enrichment_comparison.get(
            "nmdc_avg_enrichment_in_random_samples", 0
        )
        gold_rate = enrichment_comparison.get(
            "gold_avg_enrichment_in_random_samples", 0
        )

        if nmdc_rate > 0.5:
            recommendations.append(
                "NMDC has high enrichment rate - random sampling is effective"
            )
        if gold_rate > 0.5:
            recommendations.append(
                "GOLD has high enrichment rate - random sampling is effective"
            )

        if nmdc_rate < 0.1:
            recommendations.append(
                "NMDC has low enrichment rate - use targeted enrichable sampling"
            )
        if gold_rate < 0.1:
            recommendations.append(
                "GOLD has low enrichment rate - use targeted enrichable sampling"
            )

    analysis["sampling_recommendations"] = recommendations

    # Scalability assessment
    dataset_comparison = comparison.get("dataset_scale_comparison", {})
    efficiency_comparison = comparison.get("sampling_efficiency_comparison", {})

    scalability_notes = []

    if dataset_comparison:
        nmdc_total = dataset_comparison.get("nmdc_total_samples", 0)
        gold_total = dataset_comparison.get("gold_total_samples", 0)

        if nmdc_total > 100000:
            scalability_notes.append("NMDC dataset is large-scale (>100k samples)")
        if gold_total > 100000:
            scalability_notes.append("GOLD dataset is large-scale (>100k samples)")

    if efficiency_comparison:
        speed_factor = efficiency_comparison.get("speed_difference_factor", 1)
        if speed_factor > 2:
            scalability_notes.append(
                f"Significant performance difference between sources (factor: {speed_factor})"
            )

    analysis["scalability_assessment"] = {
        "notes": scalability_notes,
        "large_scale_ready": len(
            [note for note in scalability_notes if "large-scale" in note]
        )
        > 0,
    }

    return analysis


def test_unified_random_sampling() -> dict[str, Any]:
    """Test unified fetcher random sampling across multiple sources."""
    connection_string = get_mongo_connection_string()

    unified_fetcher = UnifiedBiosampleFetcher()
    unified_fetcher.configure_nmdc_mongo(connection_string, "nmdc", "biosample_set")
    unified_fetcher.configure_gold_mongo(
        connection_string, "gold_metadata", "biosamples"
    )

    results: dict[str, Any] = {
        "unified_sampling_tests": [],
        "source_distribution_analysis": {},
        "cross_source_comparison": {},
    }

    try:
        # Test unified random sampling with different sizes
        sample_sizes = [10, 25, 50]

        for size in sample_sizes:
            # Test combined sampling
            start_time = time.time()
            combined_samples = list(
                unified_fetcher.fetch_random_locations(n=size, source="all")
            )
            combined_time = time.time() - start_time

            # Analyze source distribution
            source_distribution = {"NMDC": 0, "GOLD": 0}
            for sample in combined_samples:
                if (
                    sample.database_source
                    and sample.database_source in source_distribution
                ):
                    source_distribution[sample.database_source] += 1

            # Test source-specific sampling for comparison
            start_time = time.time()
            nmdc_samples = list(
                unified_fetcher.fetch_random_locations(n=size // 2, source="nmdc")
            )
            nmdc_time = time.time() - start_time

            start_time = time.time()
            gold_samples = list(
                unified_fetcher.fetch_random_locations(n=size // 2, source="gold")
            )
            gold_time = time.time() - start_time

            test_result = {
                "sample_size_requested": size,
                "combined_sampling": {
                    "samples_returned": len(combined_samples),
                    "sampling_time_seconds": round(combined_time, 4),
                    "source_distribution": source_distribution,
                    "enrichable_count": sum(
                        1 for s in combined_samples if s.is_enrichable()
                    ),
                },
                "separate_sampling": {
                    "nmdc_samples": len(nmdc_samples),
                    "gold_samples": len(gold_samples),
                    "nmdc_time_seconds": round(nmdc_time, 4),
                    "gold_time_seconds": round(gold_time, 4),
                    "total_separate_time": round(nmdc_time + gold_time, 4),
                },
                "efficiency_comparison": {
                    "combined_faster": combined_time < (nmdc_time + gold_time),
                    "time_difference": round(
                        abs(combined_time - (nmdc_time + gold_time)), 4
                    ),
                },
            }

            unified_tests = results["unified_sampling_tests"]
            if isinstance(unified_tests, list):
                unified_tests.append(test_result)

        # Analyze source distribution patterns
        if results["unified_sampling_tests"]:
            all_distributions = [
                test["combined_sampling"]["source_distribution"]
                for test in results["unified_sampling_tests"]
            ]

            results["source_distribution_analysis"] = {
                "distribution_consistency": _analyze_distribution_consistency(
                    all_distributions
                ),
                "average_nmdc_proportion": sum(d["NMDC"] for d in all_distributions)
                / sum(d["NMDC"] + d["GOLD"] for d in all_distributions),
                "average_gold_proportion": sum(d["GOLD"] for d in all_distributions)
                / sum(d["NMDC"] + d["GOLD"] for d in all_distributions),
            }

        # Cross-source comparison
        unified_tests_list = results["unified_sampling_tests"]
        if isinstance(unified_tests_list, list) and len(unified_tests_list) >= 2:
            first_test = unified_tests_list[0]
            last_test = unified_tests_list[-1]

            results["cross_source_comparison"] = {
                "scalability_factor": last_test["sample_size_requested"]
                / first_test["sample_size_requested"],
                "time_scalability": last_test["combined_sampling"][
                    "sampling_time_seconds"
                ]
                / first_test["combined_sampling"]["sampling_time_seconds"],
                "distribution_stability": abs(
                    last_test["combined_sampling"]["source_distribution"]["NMDC"]
                    / last_test["combined_sampling"]["samples_returned"]
                    - first_test["combined_sampling"]["source_distribution"]["NMDC"]
                    / first_test["combined_sampling"]["samples_returned"]
                )
                < 0.2,
            }

    except Exception as e:
        results["error"] = {
            "message": "Error during unified random sampling test",
            "details": str(e),
        }

    return results


def _analyze_distribution_consistency(
    distributions: list[dict[str, int]],
) -> dict[str, Any]:
    """Analyze consistency of source distributions across multiple samples."""
    if not distributions:
        return {"consistency": "no_data"}

    nmdc_proportions = []
    gold_proportions = []

    for dist in distributions:
        total = dist["NMDC"] + dist["GOLD"]
        if total > 0:
            nmdc_proportions.append(dist["NMDC"] / total)
            gold_proportions.append(dist["GOLD"] / total)

    if not nmdc_proportions:
        return {"consistency": "no_valid_distributions"}

    nmdc_variance = _calculate_variance(nmdc_proportions)
    gold_variance = _calculate_variance(gold_proportions)

    return {
        "nmdc_proportion_variance": round(nmdc_variance, 4),
        "gold_proportion_variance": round(gold_variance, 4),
        "distribution_stable": nmdc_variance < 0.1 and gold_variance < 0.1,
        "consistency_rating": "high"
        if nmdc_variance < 0.05
        else "medium"
        if nmdc_variance < 0.15
        else "low",
    }


def demonstrate_random_sampling(_connection_string: str) -> dict[str, Any]:
    """Demonstrate comprehensive random sampling functionality."""
    results = {
        "demonstration_info": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "description": "Random sampling demonstration using MongoDB aggregation pipelines",
            "connection_source": "environment"
            if "MONGO_URI" in os.environ
            else "default",
        },
        "mongodb_sampling_tests": {},
        "unified_sampling_tests": {},
        "sampling_methodology_analysis": {},
        "performance_recommendations": [],
    }

    try:
        # Test MongoDB-specific sampling
        results["mongodb_sampling_tests"] = test_mongodb_random_sampling()

        # Test unified sampling
        results["unified_sampling_tests"] = test_unified_random_sampling()

        # Analyze sampling methodologies
        results["sampling_methodology_analysis"] = _analyze_sampling_methodologies(
            results
        )

        # Generate performance recommendations
        results["performance_recommendations"] = _generate_performance_recommendations(
            results
        )

    except Exception as e:
        results["error"] = {
            "message": "Error during random sampling demonstration",
            "details": str(e),
        }

    return results


def _analyze_sampling_methodologies(results: dict[str, Any]) -> dict[str, Any]:
    """Analyze different sampling methodologies used."""
    analysis: dict[str, Any] = {
        "methodologies_tested": [],
        "mongodb_aggregation_effectiveness": {},
        "random_vs_enrichable_sampling": {},
    }

    mongodb_tests = results.get("mongodb_sampling_tests", {})

    # Identify methodologies tested
    methodologies = []

    for source_key in ["nmdc_sampling_tests", "gold_sampling_tests"]:
        if source_key in mongodb_tests and "error" not in mongodb_tests[source_key]:
            source_tests = mongodb_tests[source_key]

            if source_tests.get("random_sampling_tests"):
                methodologies.append(f"{source_key.split('_')[0]}_random_sampling")
            if source_tests.get("enrichable_sampling_tests"):
                methodologies.append(f"{source_key.split('_')[0]}_enrichable_sampling")
            if source_tests.get("aggregation_pipeline_tests"):
                methodologies.append(f"{source_key.split('_')[0]}_aggregation_pipeline")

    analysis["methodologies_tested"] = methodologies

    # Analyze MongoDB aggregation effectiveness
    pipeline_performance = {}
    for source_key in ["nmdc_sampling_tests", "gold_sampling_tests"]:
        if source_key in mongodb_tests:
            source_tests = mongodb_tests[source_key]
            pipeline_tests = source_tests.get("aggregation_pipeline_tests", [])

            if pipeline_tests:
                avg_efficiency = sum(
                    test["pipeline_efficiency"] for test in pipeline_tests
                ) / len(pipeline_tests)
                pipeline_performance[source_key.split("_")[0]] = {
                    "average_samples_per_second": round(avg_efficiency, 2),
                    "tests_performed": len(pipeline_tests),
                }

    analysis["mongodb_aggregation_effectiveness"] = pipeline_performance

    # Compare random vs enrichable sampling
    comparison = {}
    for source_key in ["nmdc_sampling_tests", "gold_sampling_tests"]:
        if source_key in mongodb_tests:
            source_tests = mongodb_tests[source_key]
            random_tests = source_tests.get("random_sampling_tests", [])
            enrichable_tests = source_tests.get("enrichable_sampling_tests", [])

            if random_tests and enrichable_tests:
                random_avg_time = sum(
                    test["avg_time_per_sample"] for test in random_tests
                ) / len(random_tests)
                enrichable_avg_time = sum(
                    test["avg_time_per_sample"] for test in enrichable_tests
                ) / len(enrichable_tests)

                comparison[source_key.split("_")[0]] = {
                    "random_sampling_avg_time": round(random_avg_time, 6),
                    "enrichable_sampling_avg_time": round(enrichable_avg_time, 6),
                    "enrichable_sampling_faster": enrichable_avg_time < random_avg_time,
                    "speed_difference_factor": round(
                        random_avg_time / enrichable_avg_time, 2
                    )
                    if enrichable_avg_time > 0
                    else 0,
                }

    analysis["random_vs_enrichable_sampling"] = comparison

    return analysis


def _generate_performance_recommendations(results: dict[str, Any]) -> list[str]:
    """Generate performance recommendations based on test results."""
    recommendations = []

    mongodb_tests = results.get("mongodb_sampling_tests", {})
    unified_tests = results.get("unified_sampling_tests", {})

    # MongoDB-specific recommendations
    if "sampling_comparison" in mongodb_tests:
        comparison = mongodb_tests["sampling_comparison"]

        if "sampling_efficiency_comparison" in comparison:
            efficiency = comparison["sampling_efficiency_comparison"]
            faster_source = efficiency.get("faster_source")
            speed_factor = efficiency.get("speed_difference_factor", 1)

            if speed_factor > 2:
                recommendations.append(
                    f"Use {faster_source} for better sampling performance (factor: {speed_factor}x)"
                )

        if "dataset_scale_comparison" in comparison:
            scale = comparison["dataset_scale_comparison"]
            nmdc_rate = scale.get("nmdc_enrichable_rate", 0)
            gold_rate = scale.get("gold_enrichable_rate", 0)

            if nmdc_rate > 0.7:
                recommendations.append(
                    "NMDC has high enrichment rate - random sampling is efficient"
                )
            if gold_rate > 0.7:
                recommendations.append(
                    "GOLD has high enrichment rate - random sampling is efficient"
                )

    # Unified sampling recommendations
    if "unified_sampling_tests" in unified_tests and isinstance(
        unified_tests["unified_sampling_tests"], list
    ):
        unified_test_list = unified_tests["unified_sampling_tests"]

        if unified_test_list:
            # Check if combined sampling is consistently faster
            faster_combined_count = sum(
                1
                for test in unified_test_list
                if test.get("efficiency_comparison", {}).get("combined_faster", False)
            )

            if faster_combined_count > len(unified_test_list) / 2:
                recommendations.append(
                    "Use unified sampling for better performance across multiple sources"
                )

            # Check distribution stability
            if "source_distribution_analysis" in unified_tests:
                distribution = unified_tests["source_distribution_analysis"]
                if distribution.get("distribution_stable", False):
                    recommendations.append(
                        "Source distribution is stable - unified sampling provides consistent results"
                    )

    # Aggregation pipeline recommendations
    methodology_analysis = results.get("sampling_methodology_analysis", {})
    if "mongodb_aggregation_effectiveness" in methodology_analysis:
        pipeline_perf = methodology_analysis["mongodb_aggregation_effectiveness"]

        for source, perf in pipeline_perf.items():
            if perf.get("average_samples_per_second", 0) > 100:
                recommendations.append(
                    f"MongoDB aggregation pipeline for {source} is highly efficient (>{perf['average_samples_per_second']} samples/sec)"
                )

    # Fallback recommendation
    if not recommendations:
        recommendations.append(
            "Use MongoDB aggregation pipelines for optimal random sampling performance"
        )

    return recommendations


@click.command()
@click.option("--output-file", "-o", help="Output file path (default: stdout)")
@click.option("--indent", default=2, help="JSON indentation level", type=int)
@click.option(
    "--mongo-uri", help="MongoDB connection URI (default: environment or hardcoded)"
)
def main(output_file: str, indent: int, mongo_uri: str):
    """Run the random sampling demonstration and output results as JSON."""
    try:
        connection_string = get_mongo_connection_string(mongo_uri)
        results = demonstrate_random_sampling(connection_string)
        output = json.dumps(results, indent=indent, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            click.echo(f"Results written to {output_file}")
        else:
            print(output)
    except Exception as e:
        error_result = {
            "error": "Failed to run random sampling demonstration",
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
