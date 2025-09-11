#!/usr/bin/env python3
"""
Elevation service demonstrations and batch processing utilities.

This module provides specialized functions for demonstrating elevation lookups
with biosamples and creating various output formats.
"""

import csv
import json
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .elevation.service import ElevationService
from .logging_config import get_logger, setup_logging
from .models import ElevationRequest

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
    """Elevation service demonstrations and batch processing."""
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
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file for results",
)
@click.option("--timeout", default=30.0, type=float, help="Request timeout in seconds")
@click.option("--no-cache", is_flag=True, help="Disable caching")
@click.option("--providers", help="Comma-separated list of preferred providers")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["jsonl", "csv", "json"]),
    default="jsonl",
    help="Output format",
)
def process_biosamples(
    input_file: Path,
    output_file: Path,
    timeout: float,
    no_cache: bool,
    providers: str,
    output_format: str,
) -> None:
    """Process elevation lookups for synthetic biosamples JSON file."""

    def run_processing() -> None:
        try:
            # Load biosamples
            console.print(f"📁 Loading biosamples from {input_file}")
            with open(input_file) as f:
                biosamples = json.load(f)

            # Filter samples with valid coordinates
            valid_samples = []
            for sample in biosamples:
                geo = sample.get("geo", {})
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat is not None and lon is not None:
                    valid_samples.append(sample)

            console.print(
                f"📍 Found {len(valid_samples)} samples with coordinates (out of {len(biosamples)} total)"
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

            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Process samples sequentially with progress tracking
            results = []

            with Progress() as progress:
                task = progress.add_task(
                    "Processing biosamples...", total=len(valid_samples)
                )

                for sample in valid_samples:
                    geo = sample["geo"]
                    sample_id = sample.get(
                        "nmdc_biosample_id", sample.get("name", "unknown")
                    )

                    request = ElevationRequest(
                        latitude=geo["latitude"],
                        longitude=geo["longitude"],
                        preferred_providers=provider_list,
                    )

                    try:
                        observations = service.get_elevation(
                            request,
                            timeout_s=timeout,
                            read_from_cache=use_cache,
                            write_to_cache=use_cache,
                        )

                        envelope = service.create_output_envelope(
                            sample_id, observations
                        )

                        # Get best elevation for summary
                        best = service.get_best_elevation(observations)

                        result = {
                            "sample": sample,
                            "envelope": envelope,
                            "best_elevation": best.elevation_meters if best else None,
                            "best_provider": best.provider if best else None,
                            "num_providers": len(
                                [
                                    obs
                                    for obs in observations
                                    if obs.value_status.value == "ok"
                                ]
                            ),
                        }

                        progress.advance(task)
                        results.append(result)

                    except Exception as e:
                        logger.error(f"Failed to process {sample_id}: {e}")
                        progress.advance(task)
                        results.append(
                            {
                                "sample": sample,
                                "error": str(e),
                                "best_elevation": None,
                                "best_provider": None,
                                "num_providers": 0,
                            }
                        )

            # Write output in requested format
            console.print(f"💾 Writing results to {output_file}")

            if output_format == "jsonl":
                with open(output_file, "w") as f:
                    for result in results:
                        if "envelope" in result:
                            json.dump(result["envelope"].model_dump(), f, default=str)
                            f.write("\n")

            elif output_format == "json":
                output_data = []
                for result in results:
                    if "envelope" in result:
                        output_data.append(result["envelope"].model_dump())
                with open(output_file, "w") as f:
                    json.dump(output_data, f, indent=2, default=str)

            elif output_format == "csv":
                with open(output_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "sample_id",
                            "name",
                            "latitude",
                            "longitude",
                            "country",
                            "best_elevation_m",
                            "best_provider",
                            "num_providers",
                            "ecosystem_category",
                        ]
                    )

                    for result in results:
                        sample = result["sample"]
                        geo = sample.get("geo", {})
                        writer.writerow(
                            [
                                sample.get("nmdc_biosample_id", ""),
                                sample.get("name", ""),
                                geo.get("latitude", ""),
                                geo.get("longitude", ""),
                                geo.get("country", ""),
                                result.get("best_elevation", ""),
                                result.get("best_provider", ""),
                                result.get("num_providers", 0),
                                sample.get("ecosystem_category", ""),
                            ]
                        )

            # Print summary
            successful = len([r for r in results if "envelope" in r])
            failed = len(results) - successful

            console.print("\n✅ Processing complete:")
            console.print(f"   • Successful: {successful}")
            console.print(f"   • Failed: {failed}")
            console.print(f"   • Output: {output_file}")

            # Show sample statistics
            elevations = [
                float(r["best_elevation"])
                for r in results
                if r.get("best_elevation") is not None
            ]
            if elevations:
                console.print("\n📊 Elevation statistics:")
                console.print(f"   • Min: {min(elevations):.1f}m")
                console.print(f"   • Max: {max(elevations):.1f}m")
                console.print(f"   • Mean: {sum(elevations) / len(elevations):.1f}m")

        except Exception as e:
            console.print(f"❌ Error: {e}")
            logger.error(f"Processing failed: {e}")
            raise

    run_processing()


@cli.command()
@click.option("--lat", type=float, required=True, help="Latitude")
@click.option("--lon", type=float, required=True, help="Longitude")
@click.option("--providers", help="Comma-separated providers to compare")
@click.option("--output", help="Output file for detailed comparison")
def compare_providers(lat: float, lon: float, providers: str, output: str) -> None:
    """Compare elevation results from different providers for a single coordinate."""

    def run_comparison() -> None:
        service = ElevationService.from_env()

        # Get provider list
        provider_list = None
        if providers:
            provider_list = [p.strip() for p in providers.split(",")]

        console.print(f"🌍 Comparing elevation providers for {lat:.6f}, {lon:.6f}")

        request = ElevationRequest(
            latitude=lat, longitude=lon, preferred_providers=provider_list
        )

        observations = service.get_elevation(request)

        # Create comparison table
        table = Table(title=f"Provider Comparison: {lat:.6f}, {lon:.6f}")
        table.add_column("Provider", style="cyan")
        table.add_column("Elevation (m)", style="green")
        table.add_column("Resolution (m)", style="yellow")
        table.add_column("Datum", style="blue")
        table.add_column("Status", style="magenta")

        for obs in observations:
            status = "✅ OK" if obs.value_status.value == "ok" else "❌ Error"
            elevation = f"{obs.value_numeric:.1f}" if obs.value_numeric else "N/A"
            resolution = (
                f"{obs.spatial_resolution_m:.0f}"
                if obs.spatial_resolution_m
                else "Unknown"
            )

            table.add_row(
                obs.provider.name,
                elevation,
                resolution,
                obs.vertical_datum or "Unknown",
                status,
            )

        console.print(table)

        # Best elevation
        best = service.get_best_elevation(observations)
        if best:
            console.print(
                f"\n🎯 Best result: {best.elevation_meters:.1f}m from {best.provider}"
            )

        # Save detailed output if requested
        if output:
            envelope = service.create_output_envelope(
                "provider-comparison", observations
            )
            with open(output, "w") as f:
                json.dump(envelope.model_dump(), f, indent=2, default=str)
            console.print(f"💾 Detailed results saved to {output}")

    run_comparison()


if __name__ == "__main__":
    cli()
