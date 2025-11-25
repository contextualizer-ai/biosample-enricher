"""CLI interface for land cover and vegetation enrichment."""

import json
from datetime import datetime
from pathlib import Path

import click

from biosample_enricher.land.service import LandService
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


@click.group()
def land():
    """Land cover and vegetation enrichment commands."""
    pass


@land.command()
@click.option("--lat", type=float, required=True, help="Latitude in decimal degrees")
@click.option("--lon", type=float, required=True, help="Longitude in decimal degrees")
@click.option(
    "--date", type=click.DateTime(formats=["%Y-%m-%d"]), help="Target date (YYYY-MM-DD)"
)
@click.option(
    "--time-window",
    type=int,
    default=16,
    help="Time window for vegetation indices (days)",
)
@click.option("--output", type=click.Path(), help="Output file path (JSON)")
@click.option("--pretty", is_flag=True, help="Pretty print JSON output")
def lookup(
    lat: float,
    lon: float,
    date: datetime | None,
    time_window: int,
    output: str | None,
    pretty: bool,
):
    """Look up land cover and vegetation data for a single location."""
    service = LandService()

    target_date = date.date() if date else None

    result = service.enrich_location(lat, lon, target_date, time_window)

    # Convert to dict for JSON serialization
    result_dict = result.model_dump(mode="json")

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            if pretty:
                json.dump(result_dict, f, indent=2, default=str)
            else:
                json.dump(result_dict, f, default=str)

        click.echo(f"Results saved to {output_path}")
    else:
        if pretty:
            click.echo(json.dumps(result_dict, indent=2, default=str))
        else:
            click.echo(json.dumps(result_dict, default=str))


@land.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True),
    required=True,
    help="Input file with coordinates (JSON or CSV)",
)
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Target date for all locations",
)
@click.option(
    "--time-window",
    type=int,
    default=16,
    help="Time window for vegetation indices (days)",
)
@click.option(
    "--output", type=click.Path(), required=True, help="Output file path (JSONL)"
)
@click.option("--batch-size", type=int, default=10, help="Batch processing size")
def batch(
    input_file: str,
    date: datetime | None,
    time_window: int,
    output: str,
    batch_size: int,
):
    """Process multiple locations from a file."""
    service = LandService()

    # Load coordinates from input file
    input_path = Path(input_file)
    coordinates = _load_coordinates(input_path)

    if not coordinates:
        click.echo("No valid coordinates found in input file", err=True)
        return

    click.echo(f"Processing {len(coordinates)} locations...")

    target_date = date.date() if date else None

    # Process in batches
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for i in range(0, len(coordinates), batch_size):
            batch_coords = coordinates[i : i + batch_size]

            results = service.enrich_batch(batch_coords, target_date, time_window)

            # Write results as JSONL
            for result in results:
                result_dict = result.model_dump(mode="json")
                f.write(json.dumps(result_dict, default=str) + "\n")

            click.echo(
                f"Processed batch {i // batch_size + 1}/{(len(coordinates) - 1) // batch_size + 1}"
            )

    click.echo(f"Results saved to {output_path}")


@land.command()
def providers():
    """Show status of all land cover and vegetation providers."""
    service = LandService()

    status = service.get_provider_status()

    click.echo("Land Cover and Vegetation Provider Status:")
    click.echo("=" * 50)

    for _provider_key, info in status.items():
        provider_type = info.get("type", "unknown")
        available = info.get("available", False)
        status_icon = "✓" if available else "✗"

        click.echo(f"{status_icon} {info['name']} ({provider_type})")
        click.echo(f"   Coverage: {info['coverage']}")

        if not available and "error" in info:
            click.echo(f"   Error: {info['error']}")

        click.echo()


@land.command()
@click.option("--lat", type=float, default=40.123, help="Test latitude")
@click.option("--lon", type=float, default=-88.456, help="Test longitude")
@click.option("--date", type=click.DateTime(formats=["%Y-%m-%d"]), help="Test date")
def test(lat: float, lon: float, date: datetime | None):
    """Test land enrichment with sample coordinates."""
    click.echo(f"Testing land enrichment for ({lat}, {lon})")

    target_date = date.date() if date else None
    if target_date:
        click.echo(f"Target date: {target_date}")

    service = LandService()

    try:
        result = service.enrich_location(lat, lon, target_date)

        click.echo("\nResults:")
        click.echo(f"Overall quality: {result.overall_quality_score:.2f}")
        click.echo(f"Providers attempted: {len(result.providers_attempted)}")
        click.echo(f"Providers successful: {len(result.providers_successful)}")

        if result.land_cover:
            click.echo(f"\nLand Cover ({len(result.land_cover)} observations):")
            for obs in result.land_cover:
                click.echo(
                    f"  • {obs.provider}: {obs.class_label} (confidence: {obs.confidence:.2f})"
                )

        if result.vegetation:
            click.echo(f"\nVegetation Indices ({len(result.vegetation)} observations):")
            for veg_obs in result.vegetation:
                indices = []
                if veg_obs.ndvi is not None:
                    indices.append(f"NDVI: {veg_obs.ndvi:.3f}")
                if veg_obs.evi is not None:
                    indices.append(f"EVI: {veg_obs.evi:.3f}")
                if veg_obs.lai is not None:
                    indices.append(f"LAI: {veg_obs.lai:.2f}")
                if veg_obs.fpar is not None:
                    indices.append(f"FPAR: {veg_obs.fpar:.3f}")

                click.echo(f"  • {veg_obs.provider}: {', '.join(indices)}")

        if result.errors:
            click.echo("\nErrors:")
            for error in result.errors:
                click.echo(f"  • {error}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


def _load_coordinates(input_path: Path) -> list[tuple[float, float]]:
    """Load coordinates from input file (JSON or CSV)."""
    coordinates = []

    try:
        if input_path.suffix.lower() == ".json":
            with open(input_path) as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        lat = item.get("lat") or item.get("latitude")
                        lon = item.get("lon") or item.get("longitude")
                        if lat is not None and lon is not None:
                            coordinates.append((float(lat), float(lon)))
                    elif isinstance(item, list | tuple) and len(item) >= 2:
                        coordinates.append((float(item[0]), float(item[1])))

        elif input_path.suffix.lower() == ".csv":
            import csv

            with open(input_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    lat = row.get("lat") or row.get("latitude")
                    lon = row.get("lon") or row.get("longitude")
                    if lat and lon:
                        coordinates.append((float(lat), float(lon)))

        else:
            click.echo(f"Unsupported file format: {input_path.suffix}", err=True)
            return []

    except Exception as e:
        click.echo(f"Error loading coordinates: {e}", err=True)
        return []

    return coordinates


if __name__ == "__main__":
    land()
