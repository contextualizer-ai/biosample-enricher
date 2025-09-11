#!/usr/bin/env python3
"""
NMDC Biosample Adapter Demonstration

Tests NMDC-specific parsing logic including:
- lat_lon field format variations (string, dict, list)
- NMDC structured date formats with has_raw_value
- Geographic location text extraction
- ID normalization and categorization
- Study association extraction
"""

import json
import sys
from datetime import datetime
from typing import Any

import click

from biosample_enricher.adapters import NMDCBiosampleAdapter


def get_sample_nmdc_biosamples() -> list[dict[str, Any]]:
    """Generate sample NMDC biosample documents with various field formats."""
    return [
        {
            # Standard format with string lat_lon
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
            "insdc_biosample_identifiers": ["SAMN02728123"],
            "gold_biosample_identifiers": ["gold:Gb0115231"],
            "_id": "507f1f77bcf86cd799439011",
        },
        {
            # Dict format lat_lon with separate coordinates
            "id": "nmdc:bsm-11-45ky2260",
            "lat_lon": {"latitude": 38.8895, "longitude": -77.0501},
            "collection_date": "2015-06-15T14:30:00Z",
            "geographic_location": "USA: Washington DC, Potomac River",
            "part_of": ["nmdc:sty-11-45ky2260", "nmdc:sty-11-45ky2261"],
            "ncbi_biosample_identifiers": ["SAMN03456789"],
            "samp_name": "DC_river_sample_001",
            "_id": "507f1f77bcf86cd799439012",
        },
        {
            # Array format lat_lon
            "id": "nmdc:bsm-11-56lz3370",
            "lat_lon": [37.7749, -122.4194],
            "collection_date": "2016",
            "sample_collection_site": "San Francisco Bay sediment",
            "alternative_identifiers": ["SF_BAY_SED_001"],
            "jgi_portal_identifiers": ["Gp0127456"],
            "_id": "507f1f77bcf86cd799439013",
        },
        {
            # Separate latitude/longitude fields
            "id": "nmdc:bsm-11-67mn4480",
            "latitude": 40.7589,
            "longitude": -73.9851,
            "collection_date": {
                "has_raw_value": "2017-03",
                "type": "nmdc:TimestampValue",
            },
            "description": {
                "has_raw_value": "NYC harbor sediment core",
                "type": "nmdc:TextValue",
            },
            "biosample_identifiers": ["NYC_HARBOR_001"],
            "external_database_identifiers": ["EBI:ERS123456"],
            "_id": "507f1f77bcf86cd799439014",
        },
        {
            # Missing coordinates (not enrichable)
            "id": "nmdc:bsm-11-78op5590",
            "collection_date": "2018-12-01",
            "location": "Soil sample from agricultural field",
            "sample_identifiers": ["SOIL_AG_001", "FIELD_SAMPLE_022"],
            "_id": "507f1f77bcf86cd799439015",
        },
        {
            # Invalid coordinates (out of range)
            "id": "nmdc:bsm-11-89qr6600",
            "lat_lon": "999.0 -999.0",
            "collection_date": {
                "has_raw_value": "2019-08-15T10:30:45Z",
                "type": "nmdc:TimestampValue",
            },
            "geo_loc_name": "Invalid coordinate example",
            "_id": "507f1f77bcf86cd799439016",
        },
    ]


def demonstrate_nmdc_adapter() -> dict[str, Any]:
    """Demonstrate NMDC adapter functionality with various sample data."""
    adapter = NMDCBiosampleAdapter()
    sample_biosamples = get_sample_nmdc_biosamples()

    results: dict[str, Any] = {
        "demonstration_info": {
            "adapter_type": "NMDC",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sample_count": len(sample_biosamples),
            "description": "NMDC biosample adapter demonstration with various field formats",
        },
        "parsing_examples": [],
        "enrichability_analysis": {},
        "id_normalization_examples": [],
        "coordinate_parsing_examples": [],
        "date_parsing_examples": [],
        "location_text_examples": [],
        "validation_results": {
            "valid_models": 0,
            "invalid_models": 0,
            "validation_errors": [],
        },
    }

    enrichable_count = 0

    for i, biosample_data in enumerate(sample_biosamples):
        try:
            # Extract using adapter
            location = adapter.extract_location(biosample_data)

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
                    if isinstance(validation_results["validation_errors"], list):
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
                "lat_lon": biosample_data.get("lat_lon"),
                "latitude": biosample_data.get("latitude"),
                "longitude": biosample_data.get("longitude"),
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
                        "parsing_method": _identify_coord_parsing_method(
                            biosample_data
                        ),
                    }
                )

            # Date parsing example
            original_date = biosample_data.get("collection_date")
            date_examples = results["date_parsing_examples"]
            if isinstance(date_examples, list):
                date_examples.append(
                    {
                        "sample_id": location.sample_id,
                        "original_format": original_date,
                        "parsed_date": location.collection_date,
                        "date_precision": location.date_precision,
                        "parsing_method": _identify_date_parsing_method(original_date),
                    }
                )

            # Location text example
            location_fields = {
                "geo_loc_name": biosample_data.get("geo_loc_name"),
                "geographic_location": biosample_data.get("geographic_location"),
                "location": biosample_data.get("location"),
                "sample_collection_site": biosample_data.get("sample_collection_site"),
                "description": biosample_data.get("description"),
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
                        "extraction_source": _identify_location_text_source(
                            biosample_data, location.textual_location or ""
                        ),
                    }
                )

            # ID normalization example
            id_example = {
                "sample_id": location.sample_id,
                "nmdc_biosample_id": location.nmdc_biosample_id,
                "gold_biosample_id": location.gold_biosample_id,
                "alternative_identifiers": location.alternative_identifiers,
                "external_database_identifiers": location.external_database_identifiers,
                "biosample_identifiers": location.biosample_identifiers,
                "sample_identifiers": location.sample_identifiers,
                "nmdc_studies": location.nmdc_studies,
                "original_fields": {
                    "id": biosample_data.get("id"),
                    "_id": str(biosample_data.get("_id", "")),
                    "associated_studies": biosample_data.get("associated_studies"),
                    "part_of": biosample_data.get("part_of"),
                },
            }

            id_examples = results["id_normalization_examples"]
            if isinstance(id_examples, list):
                id_examples.append(id_example)

        except Exception as e:
            parsing_examples_err = results["parsing_examples"]
            if isinstance(parsing_examples_err, list):
                parsing_examples_err.append(
                    {
                        "sample_index": i,
                        "sample_id": biosample_data.get("id", f"unknown_{i}"),
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
                            "sample_id": biosample_data.get("id", f"unknown_{i}"),
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
        ),
    }

    return results


def _identify_coord_parsing_method(biosample_data: dict[str, Any]) -> str:
    """Identify which coordinate parsing method was used."""
    lat_lon = biosample_data.get("lat_lon")
    if lat_lon:
        if isinstance(lat_lon, str):
            return "string_lat_lon"
        elif isinstance(lat_lon, dict):
            return "dict_lat_lon"
        elif isinstance(lat_lon, list):
            return "array_lat_lon"
    elif (
        biosample_data.get("latitude") is not None
        and biosample_data.get("longitude") is not None
    ):
        return "separate_lat_lon_fields"
    return "no_coordinates"


def _identify_date_parsing_method(date_value: Any) -> str:
    """Identify which date parsing method was used."""
    if isinstance(date_value, dict) and date_value.get("has_raw_value"):
        return "nmdc_structured_date"
    elif isinstance(date_value, str):
        if "T" in date_value:
            return "iso_datetime_string"
        elif len(date_value) >= 10:
            return "date_string_yyyy_mm_dd"
        elif len(date_value) >= 7:
            return "date_string_yyyy_mm"
        elif len(date_value) == 4:
            return "date_string_yyyy"
    return "no_date"


def _identify_location_text_source(
    biosample_data: dict[str, Any], extracted_text: str
) -> str:
    """Identify which field was used for location text extraction."""
    if not extracted_text:
        return "no_location_text"

    location_fields = [
        ("geo_loc_name", biosample_data.get("geo_loc_name")),
        ("geographic_location", biosample_data.get("geographic_location")),
        ("location", biosample_data.get("location")),
        ("sample_collection_site", biosample_data.get("sample_collection_site")),
        ("description", biosample_data.get("description")),
    ]

    for field_name, field_value in location_fields:
        if field_value:
            if isinstance(field_value, str) and field_value.strip() == extracted_text:
                return field_name
            elif isinstance(field_value, dict):
                raw_value = field_value.get("has_raw_value")
                if (
                    raw_value
                    and isinstance(raw_value, str)
                    and raw_value.strip() == extracted_text
                ):
                    return f"{field_name}_structured"

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
def main(output_file: str, indent: int) -> None:
    """Run the NMDC adapter demonstration and output results as JSON."""
    try:
        results = demonstrate_nmdc_adapter()
        output = json.dumps(results, indent=indent, default=str)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            click.echo(f"Results written to {output_file}")
        else:
            print(output)
    except Exception as e:
        error_result = {
            "error": "Failed to run NMDC adapter demonstration",
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
