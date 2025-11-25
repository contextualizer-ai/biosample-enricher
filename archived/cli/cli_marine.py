#!/usr/bin/env python3
"""
Marine enrichment CLI for biosample oceanographic context.

Command-line interface for comprehensive marine data enrichment with
multiple providers, schema mapping, and coverage metrics.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import click

from biosample_enricher.logging_config import get_logger
from biosample_enricher.marine import MarineService
from biosample_enricher.marine.providers import (
    ESACCIProvider,
    GEBCOProvider,
    NOAAOISSTProvider,
)

if TYPE_CHECKING:
    from biosample_enricher.marine.providers.base import MarineProviderBase

logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def marine_cli(debug: bool):
    """Marine enrichment CLI for biosample oceanographic context."""
    if debug:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)


@marine_cli.command()
@click.option("--lat", type=float, required=True, help="Latitude in decimal degrees")
@click.option("--lon", type=float, required=True, help="Longitude in decimal degrees")
@click.option("--date", type=str, required=True, help="Date in YYYY-MM-DD format")
@click.option(
    "--providers",
    type=str,
    default="noaa_oisst,gebco,esa_cci",
    help="Comma-separated provider list",
)
@click.option("--output", type=click.Path(), help="Output file path (JSON)")
@click.option(
    "--schema",
    type=click.Choice(["nmdc", "gold"]),
    default="nmdc",
    help="Target schema format",
)
def lookup(
    lat: float,
    lon: float,
    date: str,
    providers: str,
    output: str | None,
    schema: str,
):
    """
    Look up marine data for a specific location and date.

    Example:
        biosample-enricher marine lookup --lat 42.5 --lon -85.4 --date 2018-07-12
    """
    click.echo("🌊 Marine Data Lookup")
    click.echo(f"📍 Location: {lat}, {lon}")
    click.echo(f"📅 Date: {date}")
    click.echo(f"🔬 Schema: {schema}")

    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d").date()

        # Parse providers
        provider_names = [p.strip() for p in providers.split(",")]
        provider_objects: list[MarineProviderBase] = []

        for provider_name in provider_names:
            if provider_name == "noaa_oisst":
                provider_objects.append(NOAAOISSTProvider())
            elif provider_name == "gebco":
                provider_objects.append(GEBCOProvider())
            elif provider_name == "esa_cci":
                provider_objects.append(ESACCIProvider())
            else:
                click.echo(f"⚠️  Unknown provider: {provider_name}", err=True)

        if not provider_objects:
            click.echo("❌ No valid providers specified", err=True)
            return

        # Initialize marine service
        marine_service = MarineService(providers=provider_objects)

        # Initialize marine service
        click.echo(f"🔍 Querying {len(provider_objects)} marine providers...")

        # Create biosample-style result
        biosample = {
            "id": f"marine_lookup_{lat}_{lon}_{date}",
            "lat_lon": {"latitude": lat, "longitude": lon},
            "collection_date": {"has_raw_value": date},
        }

        enrichment_result = marine_service.get_marine_data_for_biosample(
            biosample, target_schema=schema
        )

        # Display results
        if enrichment_result["enrichment_success"]:
            click.echo("✅ Marine enrichment successful!")

            coverage_metrics = enrichment_result["coverage_metrics"]
            click.echo(
                f"📊 Coverage: {coverage_metrics['enriched_count']}/{coverage_metrics['total_possible_fields']} fields"
            )
            click.echo(
                f"📈 Enrichment: {coverage_metrics['enrichment_percentage']:.1f}%"
            )
            click.echo(f"🏷️  Quality: {coverage_metrics['data_quality']}")
            click.echo(
                f"🛰️  Providers: {', '.join(coverage_metrics['successful_providers'])}"
            )

            # Show marine parameters
            schema_mapping = enrichment_result["schema_mapping"]
            if schema_mapping:
                click.echo("\n🌊 Marine Parameters:")
                for field, value in schema_mapping.items():
                    if isinstance(value, dict) and "has_numeric_value" in value:
                        click.echo(
                            f"  {field}: {value['has_numeric_value']} {value.get('has_unit', '')}"
                        )
                    else:
                        click.echo(f"  {field}: {value}")

        else:
            click.echo("❌ Marine enrichment failed")
            click.echo(f"Error: {enrichment_result.get('error', 'Unknown error')}")

        # Save to file if requested
        if output:
            output_path = Path(output)
            with output_path.open("w") as f:
                json.dump(enrichment_result, f, indent=2, default=str)
            click.echo(f"💾 Results saved to {output_path}")

    except ValueError as e:
        click.echo(f"❌ Date parsing error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Marine lookup failed: {e}", err=True)
        logger.error(f"Marine lookup error: {e}")


@marine_cli.command()
@click.option(
    "--input",
    type=click.Path(exists=True),
    required=True,
    help="Input file with biosample data (JSON/JSONL)",
)
@click.option("--output", type=click.Path(), help="Output file path (JSON)")
@click.option(
    "--schema",
    type=click.Choice(["nmdc", "gold"]),
    default="nmdc",
    help="Target schema format",
)
@click.option("--max-samples", type=int, help="Maximum samples to process")
def batch(
    input: str,
    output: str | None,
    schema: str,
    max_samples: int | None,
):
    """
    Batch marine enrichment for multiple biosamples.

    Example:
        biosample-enricher marine batch --input samples.jsonl --output enriched.json
    """
    click.echo("🌊 Batch Marine Enrichment")

    input_path = Path(input)

    try:
        # Load biosample data
        if input_path.suffix == ".jsonl":
            biosamples = []
            with input_path.open() as f:
                for line in f:
                    if line.strip():
                        biosamples.append(json.loads(line))
        else:
            with input_path.open() as f:
                data = json.load(f)
                biosamples = data if isinstance(data, list) else [data]

        if max_samples:
            biosamples = biosamples[:max_samples]

        click.echo(f"📊 Processing {len(biosamples)} biosamples")

        # Initialize marine service
        marine_service = MarineService()

        # Process each biosample
        results = []
        successful = 0
        failed = 0

        with click.progressbar(biosamples, label="Processing samples") as samples:
            for biosample in samples:
                try:
                    result = marine_service.get_marine_data_for_biosample(
                        biosample, target_schema=schema
                    )

                    results.append(
                        {
                            "sample_id": biosample.get("id", "unknown"),
                            "marine_enrichment": result,
                        }
                    )

                    if result["enrichment_success"]:
                        successful += 1
                    else:
                        failed += 1

                except Exception as e:
                    logger.error(
                        f"Error processing sample {biosample.get('id', 'unknown')}: {e}"
                    )
                    results.append(
                        {
                            "sample_id": biosample.get("id", "unknown"),
                            "marine_enrichment": {
                                "enrichment_success": False,
                                "error": str(e),
                            },
                        }
                    )
                    failed += 1

        # Summary
        click.echo("\n📊 Batch Processing Complete")
        click.echo(f"✅ Successful: {successful}")
        click.echo(f"❌ Failed: {failed}")
        click.echo(f"📈 Success Rate: {(successful / len(biosamples)) * 100:.1f}%")

        # Save results
        if output:
            output_path = Path(output)
            with output_path.open("w") as f:
                json.dump(results, f, indent=2, default=str)
            click.echo(f"💾 Results saved to {output_path}")
        else:
            # Print summary statistics
            if successful > 0:
                total_enriched = sum(
                    r["marine_enrichment"]
                    .get("coverage_metrics", {})
                    .get("enriched_count", 0)
                    for r in results
                    if r["marine_enrichment"].get("enrichment_success", False)
                )
                click.echo(f"🌊 Total marine parameters enriched: {total_enriched}")

    except Exception as e:
        click.echo(f"❌ Batch processing failed: {e}", err=True)
        logger.error(f"Batch processing error: {e}")


@marine_cli.command()
def providers():
    """List available marine data providers and their capabilities."""
    click.echo("🌊 Available Marine Data Providers\n")

    providers = [
        NOAAOISSTProvider(),
        GEBCOProvider(),
        ESACCIProvider(),
    ]

    for provider in providers:
        info = provider.get_provider_info()
        coverage = provider.get_coverage_period()

        click.echo(f"🛰️  {info['name'].upper()}")
        click.echo(f"   Description: {info['description']}")
        click.echo(f"   Parameters: {', '.join(info['parameters'])}")
        click.echo(f"   Coverage: {coverage['start']} to {coverage['end']}")
        click.echo(
            f"   Resolution: {info['spatial_resolution']} spatial, {info['temporal_resolution']} temporal"
        )
        click.echo(
            f"   Authentication: {'Required' if info['authentication'] else 'Not required'}"
        )
        click.echo()


@marine_cli.command()
@click.option("--lat", type=float, required=True, help="Latitude in decimal degrees")
@click.option("--lon", type=float, required=True, help="Longitude in decimal degrees")
@click.option("--date", type=str, required=True, help="Date in YYYY-MM-DD format")
def test(lat: float, lon: float, date: str):
    """Test marine data providers for a specific location and date."""
    click.echo("🧪 Testing Marine Data Providers")
    click.echo(f"📍 Location: {lat}, {lon}")
    click.echo(f"📅 Date: {date}\n")

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

        providers = [
            ("NOAA OISST", NOAAOISSTProvider()),
            ("GEBCO", GEBCOProvider()),
            ("ESA CCI", ESACCIProvider()),
        ]

        for name, provider in providers:
            click.echo(f"🧪 Testing {name}...")

            try:
                available = provider.is_available(lat, lon, target_date)
                click.echo(
                    f"   Availability: {'✅ Available' if available else '❌ Not available'}"
                )

                if available:
                    result = provider.get_marine_data(lat, lon, target_date)

                    if result.overall_quality.value != "no_data":
                        click.echo(f"   Data Quality: {result.overall_quality.value}")
                        click.echo(
                            f"   Providers: {', '.join(result.successful_providers)}"
                        )

                        # Show available parameters
                        params = []
                        for param_name in [
                            "sea_surface_temperature",
                            "bathymetry",
                            "chlorophyll_a",
                        ]:
                            param_value = getattr(result, param_name)
                            if param_value is not None:
                                params.append(param_name)

                        if params:
                            click.echo(f"   Parameters: {', '.join(params)}")
                    else:
                        click.echo("   Status: ❌ No data returned")

            except Exception as e:
                click.echo(f"   Error: ❌ {e}")

            click.echo()

    except ValueError as e:
        click.echo(f"❌ Date parsing error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Provider test failed: {e}", err=True)


if __name__ == "__main__":
    marine_cli()
