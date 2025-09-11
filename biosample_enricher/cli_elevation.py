"""CLI interface for elevation lookups."""

import csv
import json
import sys
from pathlib import Path

import click
from rich.console import Console

from .elevation import ElevationService
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
def elevation_cli(log_level: str) -> None:
    """Elevation lookup CLI."""
    setup_logging(level=log_level.upper())


@elevation_cli.command(name="lookup")
@click.option("--lat", type=float, required=True, help="Latitude in decimal degrees")
@click.option("--lon", type=float, required=True, help="Longitude in decimal degrees")
@click.option(
    "--providers",
    help="Comma-separated list of preferred providers (google,usgs,osm)",
)
@click.option("--output", "-o", help="Output file path (JSON)")
@click.option("--subject-id", default="elevation-lookup", help="Subject ID for output")
@click.option("--timeout", default=20.0, type=float, help="Request timeout in seconds")
@click.option("--no-cache", is_flag=True, help="Disable caching for this request")
@click.option("--read-cache/--no-read-cache", default=True, help="Read from cache")
@click.option("--write-cache/--no-write-cache", default=True, help="Write to cache")
def lookup_elevation(
    lat: float,
    lon: float,
    providers: str | None,
    output: str | None,
    subject_id: str,
    timeout: float,
    no_cache: bool,
    read_cache: bool,
    write_cache: bool,
) -> None:
    """Look up elevation for a single coordinate."""

    def run_lookup() -> None:
        try:
            # Parse providers
            provider_list = None
            if providers:
                provider_list = [p.strip() for p in providers.split(",")]

            # Create service
            service = ElevationService.from_env()

            # Create request
            request = ElevationRequest(
                latitude=lat, longitude=lon, preferred_providers=provider_list
            )

            # Handle cache settings
            use_read_cache = read_cache and not no_cache
            use_write_cache = write_cache and not no_cache

            console.print(f"🌍 Looking up elevation for {lat:.6f}, {lon:.6f}")
            if provider_list:
                console.print(f"📡 Preferred providers: {', '.join(provider_list)}")
            if no_cache:
                console.print("🚫 Cache disabled for this request")
            elif not use_read_cache or not use_write_cache:
                console.print(
                    f"📦 Cache: read={use_read_cache}, write={use_write_cache}"
                )

            # Get observations
            observations = service.get_elevation(
                request,
                timeout_s=timeout,
                read_from_cache=use_read_cache,
                write_to_cache=use_write_cache,
            )

            # Create output envelope
            envelope = service.create_output_envelope(subject_id, observations)

            # Display results
            console.print(f"\n📊 Results from {len(observations)} providers:")
            for obs in observations:
                status_icon = "✅" if obs.value_status.value == "ok" else "❌"
                if obs.value_numeric is not None:
                    console.print(
                        f"  {status_icon} {obs.provider.name}: "
                        f"{obs.value_numeric:.1f}m "
                        f"(±{obs.spatial_resolution_m or 'unknown'}m)"
                    )
                else:
                    console.print(
                        f"  {status_icon} {obs.provider.name}: {obs.error_message}"
                    )

            # Get best elevation
            best = service.get_best_elevation(observations)
            if best:
                console.print(
                    f"\n🎯 Best elevation: {best.elevation_meters:.1f}m "
                    f"from {best.provider}"
                )

            # Save output
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w") as f:
                    json.dump(envelope.model_dump(), f, indent=2, default=str)

                console.print(f"💾 Saved results to {output_path}")
            else:
                # Print JSON to stdout
                print(json.dumps(envelope.model_dump(), indent=2, default=str))

        except Exception as e:
            logger.error(f"Elevation lookup failed: {e}")
            console.print(f"❌ Error: {e}")
            sys.exit(1)

    run_lookup()


@elevation_cli.command(name="batch")
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Input CSV/TSV file with coordinates",
)
@click.option("--output", "-o", required=True, help="Output JSONL file path")
@click.option(
    "--providers",
    help="Comma-separated list of preferred providers (google,usgs,osm)",
)
@click.option("--timeout", default=20.0, type=float, help="Request timeout in seconds")
@click.option("--lat-col", default="lat", help="Latitude column name")
@click.option("--lon-col", default="lon", help="Longitude column name")
@click.option("--id-col", default="id", help="ID column name")
@click.option("--no-cache", is_flag=True, help="Disable caching for all requests")
@click.option("--read-cache/--no-read-cache", default=True, help="Read from cache")
@click.option("--write-cache/--no-write-cache", default=True, help="Write to cache")
def batch_elevation(
    input_file: Path,
    output: str,
    providers: str | None,
    timeout: float,
    lat_col: str,
    lon_col: str,
    id_col: str,
    no_cache: bool,
    read_cache: bool,
    write_cache: bool,
) -> None:
    """Process elevation lookups from CSV/TSV file."""

    def run_batch() -> None:
        try:
            # Parse providers
            provider_list = None
            if providers:
                provider_list = [p.strip() for p in providers.split(",")]

            # Create service
            service = ElevationService.from_env()

            # Detect delimiter
            delimiter = "\t" if input_file.suffix.lower() == ".tsv" else ","

            # Read input file
            coordinates = []
            with open(input_file) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for i, row in enumerate(reader):
                    try:
                        lat = float(row[lat_col])
                        lon = float(row[lon_col])
                        subject_id = row.get(id_col, f"coord-{i}")

                        coordinates.append((subject_id, lat, lon))
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping row {i}: {e}")

            # Handle cache settings
            use_read_cache = read_cache and not no_cache
            use_write_cache = write_cache and not no_cache

            console.print(
                f"📁 Processing {len(coordinates)} coordinates from {input_file}"
            )
            if no_cache:
                console.print("🚫 Cache disabled for all requests")
            elif not use_read_cache or not use_write_cache:
                console.print(
                    f"📦 Cache: read={use_read_cache}, write={use_write_cache}"
                )

            # Create output file
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Clear output file
            if output_path.exists():
                output_path.unlink()

            # Process all coordinates sequentially
            for subject_id, lat, lon in coordinates:
                try:
                    request = ElevationRequest(
                        latitude=lat,
                        longitude=lon,
                        preferred_providers=provider_list,
                    )

                    observations = service.get_elevation(
                        request,
                        timeout_s=timeout,
                        read_from_cache=use_read_cache,
                        write_to_cache=use_write_cache,
                    )
                    envelope = service.create_output_envelope(subject_id, observations)

                    # Append to output file
                    with open(output_path, "a") as f:
                        json.dump(envelope.model_dump(), f, default=str)
                        f.write("\n")

                    # Progress
                    best = service.get_best_elevation(observations)
                    if best:
                        console.print(f"✅ {subject_id}: {best.elevation_meters:.1f}m")
                    else:
                        console.print(f"❌ {subject_id}: No elevation data")

                except Exception as e:
                    logger.error(f"Failed to process {subject_id}: {e}")
                    console.print(f"❌ {subject_id}: {e}")

            console.print(
                f"💾 Batch processing complete. Results saved to {output_path}"
            )

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            console.print(f"❌ Error: {e}")
            sys.exit(1)

    run_batch()


if __name__ == "__main__":
    elevation_cli()
