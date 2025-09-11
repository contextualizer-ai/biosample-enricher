#!/usr/bin/env python3
"""
CLI for biosample elevation enrichment using field mapping.

This CLI provides specialized commands for processing biosample collections
with automatic field mapping and elevation lookup integration.
"""

import asyncio
import csv
import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .biosample_elevation_mapper import (
    BiosampleElevationBatch,
    BiosampleElevationMapper,
)
from .elevation.service import ElevationService
from .logging_config import get_logger, setup_logging

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Set logging level",
)
def cli(log_level: str) -> None:
    """Biosample elevation enrichment CLI with automatic field mapping."""
    setup_logging(level=log_level.upper())


@cli.command()
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Input JSON file with biosamples",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "jsonl", "csv"]),
    default="json",
    help="Output format",
)
@click.option("--batch-size", default=5, type=int, help="Concurrent requests")
@click.option("--timeout", default=30.0, type=float, help="Request timeout in seconds")
@click.option("--no-cache", is_flag=True, help="Disable caching")
@click.option("--providers", help="Comma-separated list of preferred providers")
@click.option("--show-mapping", is_flag=True, help="Show field mapping analysis")
def enrich(
    input_file: Path,
    output: Path,
    output_format: str,
    batch_size: int,
    timeout: float,
    no_cache: bool,
    providers: str,
    show_mapping: bool,
) -> None:
    """Enrich biosamples with elevation data using automatic field mapping."""

    async def run_enrichment() -> None:
        try:
            # Load biosamples
            console.print(f"📁 Loading biosamples from {input_file}")
            with open(input_file) as f:
                biosamples = json.load(f)

            console.print(f"📊 Loaded {len(biosamples)} biosamples")

            # Analyze coordinate mapping
            coord_summary = BiosampleElevationBatch.get_coordinate_summary(biosamples)
            console.print("🎯 Coordinate analysis:")
            console.print(
                f"   • Valid coordinates: {coord_summary['valid_coordinates']}"
            )
            console.print(
                f"   • Missing coordinates: {coord_summary['missing_coordinates']}"
            )
            console.print(f"   • Coverage: {coord_summary['coordinate_coverage']:.1%}")

            if show_mapping:
                # Show detailed field mapping analysis
                console.print("\n📋 Field Mapping Analysis:")
                table = Table(title="Biosample Field Mapping")
                table.add_column("Sample ID", style="cyan")
                table.add_column("Coordinates", style="green")
                table.add_column("Location Context", style="yellow")

                for sample in biosamples[:5]:  # Show first 5 samples
                    sample_id = BiosampleElevationMapper.get_biosample_id(sample)
                    coords = BiosampleElevationMapper.extract_coordinates(sample)
                    context = BiosampleElevationMapper.get_location_context(sample)

                    coords_str = (
                        f"{coords[0]:.4f}, {coords[1]:.4f}" if coords else "None"
                    )
                    context_str = ", ".join(f"{k}={v}" for k, v in context.items())

                    table.add_row(
                        sample_id,
                        coords_str,
                        context_str[:50] + "..."
                        if len(context_str) > 50
                        else context_str,
                    )

                console.print(table)
                console.print()

            # Filter valid samples
            valid_samples = BiosampleElevationBatch.filter_valid_coordinates(biosamples)
            if not valid_samples:
                console.print("❌ No samples with valid coordinates found")
                return

            console.print(
                f"🚀 Processing {len(valid_samples)} samples with valid coordinates"
            )

            # Parse providers
            provider_list = None
            if providers:
                provider_list = [p.strip() for p in providers.split(",")]
                console.print(
                    f"📡 Using preferred providers: {', '.join(provider_list)}"
                )

            # Cache settings
            use_cache = not no_cache
            if no_cache:
                console.print("🚫 Cache disabled")

            # Initialize service
            service = ElevationService.from_env()

            # Process samples
            semaphore = asyncio.Semaphore(batch_size)
            results = []

            with Progress() as progress:
                task = progress.add_task(
                    "Enriching biosamples...", total=len(valid_samples)
                )

                async def process_sample(sample: dict[str, Any]) -> dict[str, Any]:
                    async with semaphore:
                        # Extract sample info using mapper
                        sample_id = BiosampleElevationMapper.get_biosample_id(sample)
                        elevation_request = (
                            BiosampleElevationMapper.create_elevation_request(
                                sample, preferred_providers=provider_list
                            )
                        )

                        if not elevation_request:
                            progress.advance(task)
                            return {
                                "sample": sample,
                                "error": "No valid coordinates found",
                            }

                        try:
                            # Get elevation observations
                            observations = service.get_elevation(
                                elevation_request,
                                timeout_s=timeout,
                                read_from_cache=use_cache,
                                write_to_cache=use_cache,
                            )

                            # Create output envelope
                            envelope = service.create_output_envelope(
                                sample_id, observations
                            )

                            # Get best elevation
                            best = service.get_best_elevation(observations)

                            # Enhanced result with original sample data
                            result = {
                                "original_sample": sample,
                                "elevation_envelope": envelope.model_dump(),
                                "best_elevation_m": best.elevation_meters
                                if best
                                else None,
                                "best_provider": best.provider if best else None,
                                "num_successful_providers": len(
                                    [
                                        obs
                                        for obs in observations
                                        if obs.value_status.value == "ok"
                                    ]
                                ),
                                "location_context": BiosampleElevationMapper.get_location_context(
                                    sample
                                ),
                            }

                            progress.advance(task)
                            return result

                        except Exception as e:
                            logger.error(f"Failed to process {sample_id}: {e}")
                            progress.advance(task)
                            return {
                                "sample": sample,
                                "error": str(e),
                                "sample_id": sample_id,
                            }

                # Process all samples concurrently
                tasks = [process_sample(sample) for sample in valid_samples]
                results = await asyncio.gather(*tasks)

            # Write output
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                console.print(f"💾 Writing results to {output}")

                if output_format == "json":
                    with open(output, "w") as f:
                        json.dump(results, f, indent=2, default=str)

                elif output_format == "jsonl":
                    with open(output, "w") as f:
                        for result in results:
                            json.dump(result, f, default=str)
                            f.write("\n")

                elif output_format == "csv":
                    with open(output, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            [
                                "sample_id",
                                "name",
                                "latitude",
                                "longitude",
                                "best_elevation_m",
                                "best_provider",
                                "num_providers",
                                "ecosystem",
                                "country",
                                "locality",
                                "error",
                            ]
                        )

                        for result in results:
                            sample = result.get(
                                "original_sample", result.get("sample", {})
                            )
                            sample_id = BiosampleElevationMapper.get_biosample_id(
                                sample
                            )
                            coords = BiosampleElevationMapper.extract_coordinates(
                                sample
                            )
                            context = result.get("location_context", {})

                            writer.writerow(
                                [
                                    sample_id,
                                    sample.get("name", ""),
                                    coords[0] if coords else "",
                                    coords[1] if coords else "",
                                    result.get("best_elevation_m", ""),
                                    result.get("best_provider", ""),
                                    result.get("num_successful_providers", 0),
                                    context.get("ecosystem", ""),
                                    context.get("country", ""),
                                    context.get("locality", ""),
                                    result.get("error", ""),
                                ]
                            )

            # Print summary
            successful = len([r for r in results if "elevation_envelope" in r])
            failed = len(results) - successful

            console.print("\n✅ Enrichment complete:")
            console.print(f"   • Successful: {successful}")
            console.print(f"   • Failed: {failed}")
            if output:
                console.print(f"   • Output: {output}")

            # Show elevation statistics
            elevations = [
                float(r["best_elevation_m"])
                for r in results
                if r.get("best_elevation_m") is not None
            ]
            if elevations:
                console.print("\n📊 Elevation statistics:")
                console.print(f"   • Count: {len(elevations)}")
                console.print(f"   • Min: {min(elevations):.1f}m")
                console.print(f"   • Max: {max(elevations):.1f}m")
                console.print(f"   • Mean: {sum(elevations) / len(elevations):.1f}m")

            # Provider usage summary
            provider_counts: dict[str, int] = {}
            for result in results:
                provider = result.get("best_provider")
                if provider:
                    provider_counts[provider] = provider_counts.get(provider, 0) + 1

            if provider_counts:
                console.print("\n🏆 Provider usage:")
                for provider, count in sorted(
                    provider_counts.items(), key=lambda x: x[1], reverse=True
                ):
                    console.print(f"   • {provider}: {count} samples")

        except Exception as e:
            console.print(f"❌ Error: {e}")
            logger.error(f"Enrichment failed: {e}")
            raise

    asyncio.run(run_enrichment())


@cli.command()
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Input JSON file with biosamples",
)
def analyze(input_file: Path) -> None:
    """Analyze biosample field mapping without performing elevation lookups."""

    console.print(f"📁 Loading biosamples from {input_file}")
    with open(input_file) as f:
        biosamples = json.load(f)

    console.print(f"📊 Analyzing {len(biosamples)} biosamples")

    # Coordinate analysis
    summary = BiosampleElevationBatch.get_coordinate_summary(biosamples)

    # Display summary table
    summary_table = Table(title="Coordinate Analysis Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Samples", str(summary["total_samples"]))
    summary_table.add_row("Valid Coordinates", str(summary["valid_coordinates"]))
    summary_table.add_row("Missing Coordinates", str(summary["missing_coordinates"]))
    summary_table.add_row("Invalid Coordinates", str(summary["invalid_coordinates"]))
    summary_table.add_row("Coverage", f"{summary['coordinate_coverage']:.1%}")

    if "coordinate_bounds" in summary:
        bounds = summary["coordinate_bounds"]
        summary_table.add_row(
            "Latitude Range",
            f"{bounds['latitude']['min']:.4f} to {bounds['latitude']['max']:.4f}",
        )
        summary_table.add_row(
            "Longitude Range",
            f"{bounds['longitude']['min']:.4f} to {bounds['longitude']['max']:.4f}",
        )

    console.print(summary_table)

    # Detailed field mapping analysis
    console.print("\n📋 Field Mapping Details:")

    mapping_table = Table(title="Sample Field Mapping Analysis")
    mapping_table.add_column("Sample ID", style="cyan")
    mapping_table.add_column("Coordinates", style="green")
    mapping_table.add_column("Location Context", style="yellow")
    mapping_table.add_column("Status", style="magenta")

    for sample in biosamples:
        sample_id = BiosampleElevationMapper.get_biosample_id(sample)
        coords = BiosampleElevationMapper.extract_coordinates(sample)
        context = BiosampleElevationMapper.get_location_context(sample)

        if coords:
            coords_str = f"{coords[0]:.4f}, {coords[1]:.4f}"
            status = "✅ Valid"
        else:
            coords_str = "None"
            status = "❌ Missing"

        context_items = []
        for key, value in context.items():
            if value:
                context_items.append(f"{key}={value}")
        context_str = ", ".join(context_items)

        if len(context_str) > 40:
            context_str = context_str[:37] + "..."

        mapping_table.add_row(sample_id, coords_str, context_str, status)

    console.print(mapping_table)

    # Field mapping information
    console.print("\n📖 Field Mapping Reference:")
    mapping_info = BiosampleElevationMapper.get_field_mapping_info()

    console.print("🎯 Coordinate extraction strategies:")
    for strategy in mapping_info["coordinate_fields"]["primary"]["strategies"]:
        console.print(f"   • {strategy['name']}: {', '.join(strategy['fields'])}")

    console.print("🏷️  Identifier priority order:")
    for field in mapping_info["identifier_fields"]["priority_order"]:
        console.print(f"   • {field}")


@cli.command()
def show_mapping_info() -> None:
    """Display comprehensive field mapping information and examples."""

    mapping_info = BiosampleElevationMapper.get_field_mapping_info()

    console.print(
        "[bold cyan]Biosample Elevation Field Mapping Reference[/bold cyan]\n"
    )

    # Coordinate fields
    console.print("[bold green]Coordinate Extraction Strategies[/bold green]")

    for strategy in mapping_info["coordinate_fields"]["primary"]["strategies"]:
        console.print(f"\n[yellow]{strategy['name']}[/yellow]:")
        console.print(f"  Fields: {', '.join(strategy['fields'])}")
        console.print(f"  Example: {json.dumps(strategy['example'], indent=4)}")

    # Array format
    array_info = mapping_info["coordinate_fields"]["array_format"]
    console.print("\n[yellow]array_format[/yellow]:")
    console.print(f"  Description: {array_info['description']}")
    for fmt in array_info["formats"]:
        console.print(f"  {fmt['name']}: {json.dumps(fmt['example'])}")

    # Identifier fields
    console.print("\n[bold green]Identifier Fields[/bold green]")
    console.print("Priority order:")
    for field in mapping_info["identifier_fields"]["priority_order"]:
        console.print(f"  • {field}")
    console.print(f"Fallback: {mapping_info['identifier_fields']['fallback']}")

    # Context fields
    console.print("\n[bold green]Context Fields[/bold green]")
    for context_type, fields in mapping_info["context_fields"]["fields"].items():
        console.print(f"  {context_type}: {', '.join(fields)}")

    # Validation
    console.print("\n[bold green]Validation Rules[/bold green]")
    ranges = mapping_info["validation"]["coordinate_ranges"]
    console.print(
        f"  Latitude: {ranges['latitude']['min']} to {ranges['latitude']['max']}"
    )
    console.print(
        f"  Longitude: {ranges['longitude']['min']} to {ranges['longitude']['max']}"
    )
    console.print(f"  Type conversion: {mapping_info['validation']['type_conversion']}")


if __name__ == "__main__":
    cli()
