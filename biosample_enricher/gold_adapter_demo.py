#!/usr/bin/env python3
"""
GOLD Biosample Adapter Demonstration

Tests GOLD-specific parsing logic including:
- Direct latitude/longitude field extraction
- dateCollected field parsing
- GOLD location text fields (geoLocation, geographicLocation, etc.)
- GOLD ID handling and project relationships
- Study lookup from seq_projects collection
"""

import json
import sys
from datetime import datetime
from typing import Any

import click

from .adapters import GOLDBiosampleAdapter


def get_sample_gold_biosamples() -> list[dict[str, Any]]:
    """Generate sample GOLD biosample documents with various field formats."""
    return [
        {
            # Standard GOLD format
            "biosampleGoldId": "Gb0115231",
            "latitude": 42.3601,
            "longitude": -71.0928,
            "dateCollected": "2014-11-25",
            "geoLocation": "Boston Harbor, Massachusetts, USA",
            "projectGoldId": "Gp0127456",
            "habitat": "Marine sediment",
            "_id": "507f1f77bcf86cd799439021",
        },
        {
            # ISO datetime format
            "biosampleGoldId": "Gb0125342",
            "latitude": 38.8895,
            "longitude": -77.0501,
            "dateCollected": "2015-06-15T14:30:00Z",
            "geographicLocation": "Potomac River, Washington DC, USA",
            "projectGoldId": "Gp0138567",
            "sampleCollectionSite": "River sediment core site 1",
            "_id": "507f1f77bcf86cd799439022",
        },
        {
            # Year-month format date
            "biosampleGoldId": "Gb0135453",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "dateCollected": "2016-08",
            "description": "San Francisco Bay sediment sample",
            "projectGoldId": "Gp0149678",
            "alternative_identifiers": ["SF_BAY_001"],
            "nmdc_biosample_id": "nmdc:bsm-11-56lz3370",
            "_id": "507f1f77bcf86cd799439023",
        },
        {
            # Year-only date format
            "biosampleGoldId": "Gb0145564",
            "latitude": 40.7589,
            "longitude": -73.9851,
            "dateCollected": "2017",
            "geoLocation": "New York Harbor",
            "habitat": "Urban marine environment",
            "projectGoldId": "Gp0150789",
            "biosample_identifiers": ["NYC_HARBOR_SED_001"],
            "_id": "507f1f77bcf86cd799439024",
        },
        {
            # String coordinates (need conversion)
            "biosampleGoldId": "Gb0155675",
            "latitude": "33.7490",
            "longitude": "-84.3880",
            "dateCollected": "2018-12-01T09:15:30Z",
            "geographicLocation": "Atlanta, Georgia, USA",
            "sampleCollectionSite": "Urban soil sampling location",
            "projectGoldId": "Gp0161890",
            "external_database_identifiers": ["NCBI:SAMN09876543"],
            "_id": "507f1f77bcf86cd799439025",
        },
        {
            # Missing coordinates (not enrichable)
            "biosampleGoldId": "Gb0165786",
            "dateCollected": "2019-03-15",
            "description": "Agricultural soil sample without GPS coordinates",
            "projectGoldId": "Gp0172901",
            "sample_identifiers": ["AG_SOIL_SAMPLE_001"],
            "_id": "507f1f77bcf86cd799439026",
        },
        {
            # Invalid coordinates
            "biosampleGoldId": "Gb0175897",
            "latitude": 999.0,
            "longitude": -999.0,
            "dateCollected": "2020-07-20T16:45:00Z",
            "geoLocation": "Invalid coordinate test sample",
            "projectGoldId": "Gp0183012",
            "_id": "507f1f77bcf86cd799439027",
        },
        {
            # Missing date
            "biosampleGoldId": "Gb0185908",
            "latitude": 36.1627,
            "longitude": -86.7816,
            "geoLocation": "Nashville, Tennessee, USA",
            "habitat": "Freshwater lake sediment",
            "projectGoldId": "Gp0194123",
            "nmdc_biosample_id": "nmdc:bsm-11-78op5590",
            "_id": "507f1f77bcf86cd799439028",
        },
    ]


def demonstrate_gold_adapter() -> dict[str, Any]:
    """Demonstrate GOLD adapter functionality with various sample data."""
    adapter = GOLDBiosampleAdapter()
    sample_biosamples = get_sample_gold_biosamples()

    results = {
        "demonstration_info": {
            "adapter_type": "GOLD",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sample_count": len(sample_biosamples),
            "description": "GOLD biosample adapter demonstration with various field formats",
        },
        "parsing_examples": [],
        "enrichability_analysis": {},
        "id_normalization_examples": [],
        "coordinate_parsing_examples": [],
        "date_parsing_examples": [],
        "location_text_examples": [],
        "study_lookup_examples": [],
        "validation_results": {
            "valid_models": 0,
            "invalid_models": 0,
            "validation_errors": [],
        },
    }

    enrichable_count = 0

    for i, biosample_data in enumerate(sample_biosamples):
        try:
            # Extract using adapter (without database for this demo)
            location = adapter.extract_location(biosample_data, database=None)

            # Validate with Pydantic
            is_valid = True
            validation_error = None
            try:
                # Test serialization/deserialization
                location.to_dict()
                validation_results = results["validation_results"]
                if isinstance(validation_results, dict):
                    validation_results["valid_models"] += 1
            except Exception as e:
                is_valid = False
                validation_error = str(e)
                validation_results = results["validation_results"]
                if isinstance(validation_results, dict):
                    validation_results["invalid_models"] += 1
                    if isinstance(validation_results.get("validation_errors"), list):
                        validation_results["validation_errors"].append(
                            {"sample_id": location.sample_id, "error": validation_error}
                        )

            # Count enrichable samples
            if location.is_enrichable():
                enrichable_count += 1

            # Store parsing example
            parsing_example = {
                "sample_index": i,
                "sample_id": location.sample_id,
                "database_source": location.database_source,
                "is_enrichable": location.is_enrichable(),
                "location_completeness": location.location_completeness,
                "pydantic_valid": is_valid,
                "extracted_data": {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "collection_date": location.collection_date,
                    "textual_location": location.textual_location,
                    "coordinate_precision": location.coordinate_precision,
                    "date_precision": location.date_precision,
                },
            }

            if validation_error:
                parsing_example["validation_error"] = validation_error

            parsing_examples = results["parsing_examples"]
            if isinstance(parsing_examples, list):
                parsing_examples.append(parsing_example)

            # Coordinate parsing example
            original_coords = {
                "latitude": biosample_data.get("latitude"),
                "longitude": biosample_data.get("longitude"),
                "data_types": {
                    "latitude": type(biosample_data.get("latitude")).__name__
                    if biosample_data.get("latitude") is not None
                    else None,
                    "longitude": type(biosample_data.get("longitude")).__name__
                    if biosample_data.get("longitude") is not None
                    else None,
                },
            }

            coord_examples = results["coordinate_parsing_examples"]
            if isinstance(coord_examples, list):
                coord_examples.append(
                    {
                        "sample_id": location.sample_id,
                        "original_format": original_coords,
                        "parsed_coords": {
                            "latitude": location.latitude,
                            "longitude": location.longitude,
                            "precision": location.coordinate_precision,
                        },
                        "conversion_needed": _check_coordinate_conversion(
                            biosample_data
                        ),
                    }
                )

            # Date parsing example
            original_date = biosample_data.get("dateCollected")
            date_examples = results["date_parsing_examples"]
            if isinstance(date_examples, list):
                date_examples.append(
                    {
                        "sample_id": location.sample_id,
                        "original_format": original_date,
                        "parsed_date": location.collection_date,
                        "date_precision": location.date_precision,
                        "parsing_method": _identify_gold_date_parsing_method(
                            original_date
                        ),
                    }
                )

            # Location text example
            location_fields = {
                "geoLocation": biosample_data.get("geoLocation"),
                "geographicLocation": biosample_data.get("geographicLocation"),
                "sampleCollectionSite": biosample_data.get("sampleCollectionSite"),
                "description": biosample_data.get("description"),
                "habitat": biosample_data.get("habitat"),
            }

            location_examples = results["location_text_examples"]
            if isinstance(location_examples, list):
                location_examples.append(
                    {
                        "sample_id": location.sample_id,
                        "available_fields": {
                            k: v for k, v in location_fields.items() if v is not None
                        },
                        "extracted_text": location.textual_location,
                        "extraction_source": _identify_gold_location_text_source(
                            biosample_data, location.textual_location or ""
                        ),
                    }
                )

            # ID normalization example
            id_example = {
                "sample_id": location.sample_id,
                "gold_biosample_id": location.gold_biosample_id,
                "nmdc_biosample_id": location.nmdc_biosample_id,
                "alternative_identifiers": location.alternative_identifiers,
                "external_database_identifiers": location.external_database_identifiers,
                "biosample_identifiers": location.biosample_identifiers,
                "sample_identifiers": location.sample_identifiers,
                "gold_studies": location.gold_studies,
                "original_fields": {
                    "biosampleGoldId": biosample_data.get("biosampleGoldId"),
                    "projectGoldId": biosample_data.get("projectGoldId"),
                    "_id": str(biosample_data.get("_id", "")),
                    "nmdc_biosample_id": biosample_data.get("nmdc_biosample_id"),
                },
            }

            id_examples = results["id_normalization_examples"]
            if isinstance(id_examples, list):
                id_examples.append(id_example)

            # Study lookup example (simulated since we don't have database)
            study_lookup_example = {
                "sample_id": location.sample_id,
                "biosample_gold_id": location.gold_biosample_id,
                "project_gold_id": biosample_data.get("projectGoldId"),
                "study_lookup_attempted": True,
                "study_lookup_result": "simulated - would query seq_projects collection",
                "note": "Requires database connection for actual lookup",
            }

            study_examples = results["study_lookup_examples"]
            if isinstance(study_examples, list):
                study_examples.append(study_lookup_example)

        except Exception as e:
            parsing_examples_err = results["parsing_examples"]
            if isinstance(parsing_examples_err, list):
                parsing_examples_err.append(
                    {
                        "sample_index": i,
                        "sample_id": biosample_data.get(
                            "biosampleGoldId", f"unknown_{i}"
                        ),
                        "error": str(e),
                        "is_enrichable": False,
                        "pydantic_valid": False,
                    }
                )
            validation_results = results["validation_results"]
            if isinstance(validation_results, dict):
                validation_results["invalid_models"] += 1
                if isinstance(validation_results.get("validation_errors"), list):
                    validation_results["validation_errors"].append(
                        {
                            "sample_id": biosample_data.get(
                                "biosampleGoldId", f"unknown_{i}"
                            ),
                            "error": str(e),
                        }
                    )

    # Enrichability analysis
    results["enrichability_analysis"] = {
        "total_samples": len(sample_biosamples),
        "enrichable_samples": enrichable_count,
        "enrichable_rate": enrichable_count / len(sample_biosamples)
        if sample_biosamples
        else 0.0,
        "non_enrichable_reasons": _analyze_non_enrichable_reasons(
            results["parsing_examples"]
            if isinstance(results["parsing_examples"], list)
            else []
        ),
    }

    return results


def _check_coordinate_conversion(biosample_data: dict[str, Any]) -> dict[str, bool]:
    """Check if coordinate conversion from string to float was needed."""
    lat = biosample_data.get("latitude")
    lon = biosample_data.get("longitude")

    return {
        "latitude_conversion": isinstance(lat, str) if lat is not None else False,
        "longitude_conversion": isinstance(lon, str) if lon is not None else False,
    }


def _identify_gold_date_parsing_method(date_value: Any) -> str:
    """Identify which date parsing method was used."""
    if not date_value:
        return "no_date"

    if isinstance(date_value, str):
        if "T" in date_value:
            return "iso_datetime_string"
        elif len(date_value) >= 10:
            return "date_string_yyyy_mm_dd"
        elif len(date_value) >= 7:
            return "date_string_yyyy_mm"
        elif len(date_value) == 4:
            return "date_string_yyyy"

    return "unknown_date_format"


def _identify_gold_location_text_source(
    biosample_data: dict[str, Any], extracted_text: str
) -> str:
    """Identify which field was used for location text extraction."""
    if not extracted_text:
        return "no_location_text"

    location_fields = [
        ("geoLocation", biosample_data.get("geoLocation")),
        ("geographicLocation", biosample_data.get("geographicLocation")),
        ("sampleCollectionSite", biosample_data.get("sampleCollectionSite")),
        ("description", biosample_data.get("description")),
        ("habitat", biosample_data.get("habitat")),
    ]

    for field_name, field_value in location_fields:
        if (
            field_value
            and isinstance(field_value, str)
            and field_value.strip() == extracted_text
        ):
            return field_name

    return "unknown_source"


def _analyze_non_enrichable_reasons(
    parsing_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Analyze why samples are not enrichable."""
    reasons = []

    for example in parsing_examples:
        if not example.get("is_enrichable", False):
            extracted = example.get("extracted_data", {})
            sample_id = example.get("sample_id", "unknown")

            reason = {"sample_id": sample_id, "reasons": []}

            if extracted.get("latitude") is None:
                reason["reasons"].append("missing_latitude")
            elif not (-90 <= extracted["latitude"] <= 90):
                reason["reasons"].append("invalid_latitude_range")

            if extracted.get("longitude") is None:
                reason["reasons"].append("missing_longitude")
            elif not (-180 <= extracted["longitude"] <= 180):
                reason["reasons"].append("invalid_longitude_range")

            if "error" in example:
                reason["reasons"].append(f"parsing_error: {example['error']}")

            reasons.append(reason)

    return reasons


@click.command()
@click.option("--output-file", "-o", help="Output file path (default: stdout)")
@click.option("--indent", default=2, help="JSON indentation level", type=int)
def main(output_file: str, indent: int):
    """Run the GOLD adapter demonstration and output results as JSON."""
    try:
        results = demonstrate_gold_adapter()
        output = json.dumps(results, indent=indent, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            click.echo(f"Results written to {output_file}")
        else:
            print(output)
    except Exception as e:
        error_result = {
            "error": "Failed to run GOLD adapter demonstration",
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
