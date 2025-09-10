#!/usr/bin/env python3
"""
Synthetic Biosample Validation Demonstration

Validates synthetic biosample data against the BiosampleLocation model,
mapping nested synthetic data structure to the normalized model fields.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from pydantic import ValidationError

from .models import BiosampleLocation


def map_synthetic_to_model(synthetic_data: dict[str, Any]) -> dict[str, Any]:
    """Map synthetic biosample fields to BiosampleLocation model fields."""
    geo = synthetic_data.get("geo", {})

    # Build textual location from geo components
    location_parts = []
    for part in [geo.get("locality"), geo.get("admin1"), geo.get("country")]:
        if part:
            location_parts.append(part)
    textual_location = ", ".join(location_parts) if location_parts else None

    return {
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "collection_date": synthetic_data.get("collection_date"),
        "textual_location": textual_location,
        "sample_id": synthetic_data.get("nmdc_biosample_id")
        or synthetic_data.get("gold_biosample_id"),
        "database_source": synthetic_data.get("source_system"),
        "nmdc_biosample_id": synthetic_data.get("nmdc_biosample_id"),
        "gold_biosample_id": synthetic_data.get("gold_biosample_id"),
        # Other fields will default to None
    }


def validate_synthetic_biosamples(input_file: Path) -> dict[str, Any]:
    """Validate synthetic biosamples and return results."""
    with open(input_file) as f:
        biosamples = json.load(f)

    results: dict[str, Any] = {
        "total_samples": len(biosamples),
        "valid_samples": [],
        "invalid_samples": [],
        "validation_summary": {},
    }

    for i, biosample in enumerate(biosamples):
        sample_result: dict[str, Any] = {
            "index": i + 1,
            "original_data": biosample,
            "mapped_data": None,
            "location_model": None,
            "is_valid": False,
            "is_enrichable": False,
            "errors": [],
        }

        try:
            # Map the synthetic data to model fields
            mapped_data = map_synthetic_to_model(biosample)
            sample_result["mapped_data"] = mapped_data

            # Try to create a BiosampleLocation from the mapped data
            location = BiosampleLocation(**mapped_data)
            sample_result["location_model"] = location.to_dict()
            sample_result["is_valid"] = True
            sample_result["is_enrichable"] = location.is_enrichable()

            results["valid_samples"].append(sample_result)

        except ValidationError as e:
            sample_result["errors"] = [
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                }
                for error in e.errors()
            ]
            results["invalid_samples"].append(sample_result)

        except Exception as e:
            sample_result["errors"] = [{"field": "general", "message": str(e)}]
            results["invalid_samples"].append(sample_result)

    # Generate summary
    results["validation_summary"] = {
        "total_count": len(biosamples),
        "valid_count": len(results["valid_samples"]),
        "invalid_count": len(results["invalid_samples"]),
        "enrichable_count": sum(
            1 for sample in results["valid_samples"] if sample["is_enrichable"]
        ),
        "validation_rate": len(results["valid_samples"]) / len(biosamples)
        if biosamples
        else 0,
        "enrichable_rate": sum(
            1 for sample in results["valid_samples"] if sample["is_enrichable"]
        )
        / len(biosamples)
        if biosamples
        else 0,
    }

    return results


@click.command()
@click.option(
    "--input-file",
    "-i",
    default="data/input/synthetic_biosamples.json",
    help="Input synthetic biosamples JSON file",
)
@click.option(
    "--output-file", "-o", help="Output validation results file (default: stdout)"
)
@click.option("--indent", default=2, help="JSON indentation level", type=int)
def main(input_file: str, output_file: str, indent: int) -> None:
    """Validate synthetic biosamples against the BiosampleLocation model."""
    try:
        input_path = Path(input_file)

        if not input_path.exists():
            click.echo(f"Error: {input_path} not found", err=True)
            sys.exit(1)

        click.echo(f"Validating synthetic biosamples from {input_path}...")
        click.echo()

        results = validate_synthetic_biosamples(input_path)

        # Print summary
        summary = results["validation_summary"]
        click.echo("📊 Validation Summary:")
        click.echo(f"   Total samples: {summary['total_count']}")
        click.echo(
            f"   Valid samples: {summary['valid_count']} ({summary['validation_rate']:.1%})"
        )
        click.echo(f"   Invalid samples: {summary['invalid_count']}")
        click.echo(
            f"   Enrichable samples: {summary['enrichable_count']} ({summary['enrichable_rate']:.1%})"
        )
        click.echo()

        # Print valid samples
        for sample in results["valid_samples"]:
            location = sample["location_model"]
            click.echo(
                f"✅ Sample {sample['index']}: Valid ({'enrichable' if sample['is_enrichable'] else 'not enrichable'})"
            )
            click.echo(f"   ID: {location['sample_id']}")
            click.echo(f"   Location: {location['textual_location']}")
            click.echo(
                f"   Coordinates: {location['latitude']}, {location['longitude']}"
            )
            click.echo()

        # Print invalid samples
        for sample in results["invalid_samples"]:
            click.echo(f"❌ Sample {sample['index']}: Invalid")
            for error in sample["errors"]:
                click.echo(f"   {error['field']}: {error['message']}")
            click.echo()

        # Save detailed results
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(results, f, indent=indent, default=str)
            click.echo(f"💾 Detailed results saved to {output_path}")
        else:
            # Output JSON to stdout if no output file specified
            output = json.dumps(results, indent=indent, default=str)
            print(output)

    except Exception as e:
        error_result = {
            "error": "Failed to validate synthetic biosamples",
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
