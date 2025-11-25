#!/usr/bin/env python3
"""
Pydantic Model Validation Demonstration

Tests the explicit Pydantic schema validation that replaces dataclass approach:
- Field validation (coordinate ranges, date formats, enum constraints)
- Model serialization and deserialization
- Validation error handling and reporting
- Completeness calculation and enrichment status
"""

import json
import sys
from datetime import datetime
from typing import Any

import click
from pydantic import ValidationError

from biosample_enricher.models import BiosampleLocation


def get_validation_test_cases() -> list[dict[str, Any]]:
    """Generate test cases for Pydantic validation."""
    return [
        {
            "name": "valid_complete_sample",
            "description": "Fully valid sample with all fields",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "collection_date": "2014-11-25",
                "textual_location": "Boston Harbor, Massachusetts, USA",
                "sample_id": "nmdc:bsm-11-34xj1150",
                "database_source": "NMDC",
                "nmdc_biosample_id": "nmdc:bsm-11-34xj1150",
                "coordinate_precision": 4,
                "date_precision": "day",
            },
        },
        {
            "name": "valid_minimal_enrichable",
            "description": "Minimal valid sample with just enrichable fields",
            "data": {
                "latitude": 38.8895,
                "longitude": -77.0501,
                "sample_id": "test_minimal",
                "database_source": "GOLD",
            },
        },
        {
            "name": "invalid_latitude_high",
            "description": "Invalid sample with latitude > 90",
            "data": {
                "latitude": 95.0,
                "longitude": -71.0928,
                "sample_id": "test_invalid_lat",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_latitude_low",
            "description": "Invalid sample with latitude < -90",
            "data": {
                "latitude": -95.0,
                "longitude": -71.0928,
                "sample_id": "test_invalid_lat_low",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_longitude_high",
            "description": "Invalid sample with longitude > 180",
            "data": {
                "latitude": 42.3601,
                "longitude": 185.0,
                "sample_id": "test_invalid_lon",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_longitude_low",
            "description": "Invalid sample with longitude < -180",
            "data": {
                "latitude": 42.3601,
                "longitude": -185.0,
                "sample_id": "test_invalid_lon_low",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_date_format",
            "description": "Invalid date format",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "collection_date": "25-11-2014",  # Wrong format
                "sample_id": "test_invalid_date",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_database_source",
            "description": "Invalid database source",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "sample_id": "test_invalid_db",
                "database_source": "INVALID_DB",  # Must be NMDC or GOLD
            },
        },
        {
            "name": "invalid_date_precision",
            "description": "Invalid date precision value",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "collection_date": "2014-11-25",
                "date_precision": "invalid_precision",  # Must be day, month, or year
                "sample_id": "test_invalid_precision",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_coordinate_precision",
            "description": "Invalid coordinate precision (negative)",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "coordinate_precision": -1,  # Must be >= 0
                "sample_id": "test_invalid_coord_precision",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_completeness_high",
            "description": "Invalid completeness > 1.0",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "location_completeness": 1.5,  # Must be <= 1.0
                "sample_id": "test_invalid_completeness",
                "database_source": "NMDC",
            },
        },
        {
            "name": "invalid_completeness_low",
            "description": "Invalid completeness < 0.0",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "location_completeness": -0.1,  # Must be >= 0.0
                "sample_id": "test_invalid_completeness_low",
                "database_source": "NMDC",
            },
        },
        {
            "name": "extra_fields_forbidden",
            "description": "Extra fields should be forbidden",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "sample_id": "test_extra_fields",
                "database_source": "NMDC",
                "extra_field": "this should not be allowed",  # Extra field
            },
        },
        {
            "name": "auto_timestamp_test",
            "description": "Test automatic timestamp generation",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "sample_id": "test_timestamp",
                "database_source": "NMDC",
                # extraction_timestamp should be auto-generated
            },
        },
        {
            "name": "completeness_calculation_test",
            "description": "Test automatic completeness calculation",
            "data": {
                "latitude": 42.3601,
                "longitude": -71.0928,
                "collection_date": "2014-11-25",
                "textual_location": "Test location",
                "sample_id": "test_completeness",
                "database_source": "NMDC",
                # location_completeness should be calculated as 1.0
            },
        },
    ]


def test_pydantic_validation_case(test_case: dict[str, Any]) -> dict[str, Any]:
    """Test a single validation case."""
    result = {
        "test_name": test_case["name"],
        "description": test_case["description"],
        "input_data": test_case["data"],
        "validation_result": {},
    }

    try:
        # Try to create the model
        location = BiosampleLocation(**test_case["data"])

        # If successful, extract key information
        result["validation_result"] = {
            "valid": True,
            "model_created": True,
            "is_enrichable": location.is_enrichable(),
            "location_completeness": location.location_completeness,
            "extraction_timestamp_set": location.extraction_timestamp is not None,
            "serialized_data": location.to_dict(),
        }

        # Test serialization/deserialization
        try:
            dict_data = location.model_dump()
            recreated = BiosampleLocation(**dict_data)
            result["validation_result"]["serialization_test"] = {
                "serializable": True,
                "deserializable": True,
                "data_preserved": recreated.sample_id == location.sample_id,
            }
        except Exception as e:
            result["validation_result"]["serialization_test"] = {
                "serializable": False,
                "error": str(e),
            }

    except ValidationError as e:
        # Validation failed as expected
        result["validation_result"] = {
            "valid": False,
            "model_created": False,
            "validation_errors": [
                {
                    "field": error.get("loc", ["unknown"])[0]
                    if error.get("loc")
                    else "unknown",
                    "message": error.get("msg", "unknown error"),
                    "type": error.get("type", "unknown"),
                    "input": error.get("input"),
                }
                for error in e.errors()
            ],
        }

    except Exception as e:
        # Unexpected error
        result["validation_result"] = {
            "valid": False,
            "model_created": False,
            "unexpected_error": str(e),
        }

    return result


def test_enrichment_logic() -> dict[str, Any]:
    """Test the enrichment logic specifically."""
    test_cases = [
        {
            "name": "enrichable_valid_coords",
            "data": {"latitude": 42.0, "longitude": -71.0},
            "expected_enrichable": True,
        },
        {
            "name": "not_enrichable_missing_lat",
            "data": {"longitude": -71.0},
            "expected_enrichable": False,
        },
        {
            "name": "not_enrichable_missing_lon",
            "data": {"latitude": 42.0},
            "expected_enrichable": False,
        },
        {
            "name": "not_enrichable_lat_too_high",
            "data": {"latitude": 91.0, "longitude": -71.0},
            "expected_enrichable": False,  # Should fail validation before reaching enrichment check
        },
        {
            "name": "not_enrichable_lat_too_low",
            "data": {"latitude": -91.0, "longitude": -71.0},
            "expected_enrichable": False,  # Should fail validation before reaching enrichment check
        },
        {
            "name": "enrichable_boundary_coords",
            "data": {"latitude": 90.0, "longitude": 180.0},
            "expected_enrichable": True,
        },
        {
            "name": "enrichable_negative_boundary_coords",
            "data": {"latitude": -90.0, "longitude": -180.0},
            "expected_enrichable": True,
        },
    ]

    results: list[dict[str, Any]] = []
    for case in test_cases:
        try:
            # Add required fields for model creation
            case_data = case["data"]
            assert isinstance(case_data, dict)
            test_data: dict[str, Any] = {
                "sample_id": f"test_{case['name']}",
                "database_source": "NMDC",
            }
            test_data.update(case_data)

            location = BiosampleLocation(**test_data)
            actual_enrichable = location.is_enrichable()

            results.append(
                {
                    "test_name": case["name"],
                    "input_coords": case["data"],
                    "expected_enrichable": case["expected_enrichable"],
                    "actual_enrichable": actual_enrichable,
                    "test_passed": actual_enrichable == case["expected_enrichable"],
                    "model_valid": True,
                }
            )

        except ValidationError:
            # Model validation failed - this is expected for invalid coordinates
            results.append(
                {
                    "test_name": case["name"],
                    "input_coords": case["data"],
                    "expected_enrichable": case["expected_enrichable"],
                    "actual_enrichable": None,
                    "test_passed": not case[
                        "expected_enrichable"
                    ],  # If we expected it to not be enrichable
                    "model_valid": False,
                    "note": "Model validation failed (expected for invalid coordinates)",
                }
            )
        except Exception as e:
            results.append(
                {
                    "test_name": case["name"],
                    "input_coords": case["data"],
                    "expected_enrichable": case["expected_enrichable"],
                    "actual_enrichable": None,
                    "test_passed": False,
                    "model_valid": False,
                    "error": str(e),
                }
            )

    return {
        "enrichment_tests": results,
        "summary": {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.get("test_passed", False)),
            "failed_tests": sum(1 for r in results if not r.get("test_passed", False)),
        },
    }


def demonstrate_pydantic_validation() -> dict[str, Any]:
    """Demonstrate comprehensive Pydantic validation functionality."""
    test_cases = get_validation_test_cases()

    results: dict[str, Any] = {
        "demonstration_info": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_test_cases": len(test_cases),
            "description": "Pydantic model validation demonstration with various valid and invalid inputs",
        },
        "validation_tests": [],
        "enrichment_logic_tests": {},
        "validation_summary": {},
        "pydantic_features_tested": [
            "field_validation",
            "coordinate_range_validation",
            "date_format_validation",
            "enum_constraints",
            "automatic_field_generation",
            "completeness_calculation",
            "serialization_deserialization",
            "extra_fields_forbidden",
        ],
    }

    # Run all validation test cases
    for test_case in test_cases:
        test_result = test_pydantic_validation_case(test_case)
        results["validation_tests"].append(test_result)

    # Test enrichment logic specifically
    results["enrichment_logic_tests"] = test_enrichment_logic()

    # Calculate summary statistics
    valid_count = sum(
        1
        for test in results["validation_tests"]
        if test["validation_result"].get("valid", False)
    )
    invalid_count = len(results["validation_tests"]) - valid_count

    expected_valid_cases = [
        "valid_complete_sample",
        "valid_minimal_enrichable",
        "auto_timestamp_test",
        "completeness_calculation_test",
    ]
    expected_invalid_cases = [
        "invalid_latitude_high",
        "invalid_latitude_low",
        "invalid_longitude_high",
        "invalid_longitude_low",
        "invalid_date_format",
        "invalid_database_source",
        "invalid_date_precision",
        "invalid_coordinate_precision",
        "invalid_completeness_high",
        "invalid_completeness_low",
        "extra_fields_forbidden",
    ]

    correctly_validated = 0
    for test in results["validation_tests"]:
        test_name = test["test_name"]
        is_valid = test["validation_result"].get("valid", False)

        if (
            test_name in expected_valid_cases
            and is_valid
            or test_name in expected_invalid_cases
            and not is_valid
        ):
            correctly_validated += 1

    results["validation_summary"] = {
        "total_tests": len(results["validation_tests"]),
        "valid_models": valid_count,
        "invalid_models": invalid_count,
        "expected_valid_cases": len(expected_valid_cases),
        "expected_invalid_cases": len(expected_invalid_cases),
        "correctly_validated": correctly_validated,
        "validation_accuracy": correctly_validated / len(results["validation_tests"])
        if results["validation_tests"]
        else 0,
        "enrichment_test_summary": results["enrichment_logic_tests"]["summary"],
    }

    return results


@click.command()
@click.option("--output-file", "-o", help="Output file path (default: stdout)")
@click.option("--indent", default=2, help="JSON indentation level", type=int)
def main(output_file: str, indent: int) -> None:
    """Run the Pydantic validation demonstration and output results as JSON."""
    try:
        results = demonstrate_pydantic_validation()
        output = json.dumps(results, indent=indent, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            click.echo(f"Results written to {output_file}")
        else:
            print(output)
    except Exception as e:
        error_result = {
            "error": "Failed to run Pydantic validation demonstration",
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
