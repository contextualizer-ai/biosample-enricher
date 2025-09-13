"""CLI commands for soil enrichment."""

import json
from pathlib import Path

import click

from biosample_enricher.logging_config import get_logger, setup_logging
from biosample_enricher.soil import SoilService

logger = get_logger(__name__)


@click.group()
def soil() -> None:
    """Soil enrichment commands for biosample site characterization."""
    pass


@soil.command()
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option(
    "--depth",
    default="0-5cm",
    help="Depth interval (e.g., 0-5cm, 5-15cm, 15-30cm, 30-60cm)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table", "nmdc", "gold"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def lookup(
    latitude: float, longitude: float, depth: str, output_format: str, verbose: bool
) -> None:
    """Look up soil data for a specific location.

    LATITUDE: Latitude in decimal degrees
    LONGITUDE: Longitude in decimal degrees
    """
    setup_logging(level="DEBUG" if verbose else "INFO")

    service = SoilService()

    try:
        result = service.enrich_location(latitude, longitude, depth)

        if output_format == "json":
            click.echo(json.dumps(result.model_dump(), indent=2, default=str))
        elif output_format == "nmdc":
            nmdc_data = result.to_nmdc_schema()
            click.echo(json.dumps(nmdc_data, indent=2))
        elif output_format == "gold":
            gold_data = result.to_gold_schema()
            click.echo(json.dumps(gold_data, indent=2))
        else:  # table format
            _print_soil_table(result)

    except Exception as e:
        logger.error(f"Error looking up soil data: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


@soil.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", type=click.Path(path_type=Path), help="Output file (default: stdout)"
)
@click.option("--depth", default="0-5cm", help="Depth interval for all locations")
@click.option("--lat-col", default="latitude", help="Column name for latitude")
@click.option("--lon-col", default="longitude", help="Column name for longitude")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def batch(
    input_file: Path,
    output: Path,
    depth: str,
    lat_col: str,
    lon_col: str,
    output_format: str,
    verbose: bool,
) -> None:
    """Enrich multiple locations from CSV or JSON file.

    INPUT_FILE: CSV or JSON file with location data
    """
    setup_logging(level="DEBUG" if verbose else "INFO")

    service = SoilService()

    try:
        # Load input data
        locations = _load_locations(input_file, lat_col, lon_col)

        if not locations:
            click.echo("No valid locations found in input file", err=True)
            raise click.Abort()

        click.echo(f"Processing {len(locations)} locations...")

        # Enrich locations
        results = service.enrich_batch(locations, depth)

        # Output results
        if output_format == "json":
            output_data = [result.model_dump() for result in results]
            output_json = json.dumps(output_data, indent=2, default=str)

            if output:
                output.write_text(output_json)
                click.echo(f"Results written to {output}")
            else:
                click.echo(output_json)
        else:  # CSV format
            _output_csv(results, output)

        # Print summary
        successful = sum(1 for r in results if r.quality_score > 0)
        click.echo(
            f"\nSummary: {successful}/{len(results)} locations enriched successfully"
        )

    except Exception as e:
        logger.error(f"Error in batch enrichment: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


@soil.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def providers(verbose: bool) -> None:
    """Show status of soil data providers."""
    setup_logging(level="DEBUG" if verbose else "INFO")

    service = SoilService()

    try:
        status = service.get_provider_status()

        click.echo("Soil Data Provider Status:")
        click.echo("=" * 50)

        for _name, info in status.items():
            available = "✓" if info["available"] else "✗"
            click.echo(f"\n{available} {info['name']}")
            click.echo(f"   Coverage: {info['coverage']}")

            if "error" in info:
                click.echo(f"   Error: {info['error']}")

    except Exception as e:
        logger.error(f"Error checking provider status: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e


@soil.command()
@click.argument("latitude", type=float)
@click.argument("longitude", type=float)
@click.option(
    "--provider",
    type=click.Choice(["usda_nrcs", "soilgrids"]),
    help="Test specific provider (default: test all)",
)
@click.option("--depth", default="0-5cm", help="Depth interval to test")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def test(
    latitude: float, longitude: float, provider: str, depth: str, verbose: bool
) -> None:
    """Test soil data providers at a specific location.

    LATITUDE: Latitude in decimal degrees
    LONGITUDE: Longitude in decimal degrees
    """
    setup_logging(level="DEBUG" if verbose else "INFO")

    service = SoilService()

    providers_to_test = [provider] if provider else list(service.providers.keys())

    click.echo(f"Testing soil providers at ({latitude}, {longitude})")
    click.echo("=" * 60)

    for provider_name in providers_to_test:
        provider_obj = service.providers[provider_name]

        click.echo(f"\n🧪 Testing {provider_obj.name}")

        try:
            # Test availability
            available = provider_obj.is_available()
            if not available:
                click.echo("   Status: ✗ Not available")
                continue

            click.echo("   Status: ✓ Available")

            # Test data retrieval
            result = provider_obj.get_soil_data(latitude, longitude, depth)

            click.echo(f"   Quality: {result.quality_score:.2f}")
            click.echo(f"   Observations: {len(result.observations)}")

            if result.distance_m:
                click.echo(f"   Distance: {result.distance_m:.1f}m")

            if result.observations:
                obs = result.observations[0]
                if obs.classification_usda:
                    click.echo(f"   USDA Class: {obs.classification_usda}")
                if obs.classification_wrb:
                    click.echo(f"   WRB Class: {obs.classification_wrb}")
                if obs.ph_h2o is not None:
                    click.echo(f"   pH: {obs.ph_h2o}")
                if obs.texture_class:
                    click.echo(f"   Texture: {obs.texture_class}")

            if result.errors:
                click.echo(f"   Errors: {', '.join(result.errors)}")
            if result.warnings:
                click.echo(f"   Warnings: {', '.join(result.warnings)}")

        except Exception as e:
            click.echo(f"   Error: {e}")


def _print_soil_table(result) -> None:
    """Print soil result in table format."""
    click.echo(f"\nSoil Data for ({result.latitude}, {result.longitude})")
    click.echo("=" * 60)
    click.echo(f"Provider: {result.provider}")
    click.echo(f"Quality Score: {result.quality_score:.2f}")

    if result.distance_m:
        click.echo(f"Distance: {result.distance_m:.1f}m")

    if not result.observations:
        click.echo("No soil data available")
        if result.errors:
            click.echo(f"Errors: {', '.join(result.errors)}")
        return

    for i, obs in enumerate(result.observations):
        if len(result.observations) > 1:
            click.echo(f"\nObservation {i + 1}:")
        else:
            click.echo()

        if obs.classification_usda:
            click.echo(f"  USDA Classification: {obs.classification_usda}")
            if obs.confidence_usda:
                click.echo(f"  USDA Confidence: {obs.confidence_usda:.2f}")

        if obs.classification_wrb:
            click.echo(f"  WRB Classification: {obs.classification_wrb}")
            if obs.confidence_wrb:
                click.echo(f"  WRB Confidence: {obs.confidence_wrb:.2f}")

        if obs.ph_h2o is not None:
            click.echo(f"  pH (H2O): {obs.ph_h2o}")

        if obs.texture_class:
            click.echo(f"  Texture Class: {obs.texture_class}")

        if obs.sand_percent is not None:
            click.echo(f"  Sand: {obs.sand_percent}%")
        if obs.silt_percent is not None:
            click.echo(f"  Silt: {obs.silt_percent}%")
        if obs.clay_percent is not None:
            click.echo(f"  Clay: {obs.clay_percent}%")

        if obs.organic_carbon is not None:
            click.echo(f"  Organic Carbon: {obs.organic_carbon} g/kg")

        if obs.total_nitrogen is not None:
            click.echo(f"  Total Nitrogen: {obs.total_nitrogen} g/kg")

        if obs.bulk_density is not None:
            click.echo(f"  Bulk Density: {obs.bulk_density} g/cm³")

        if obs.depth_cm:
            click.echo(f"  Depth: {obs.depth_cm}")


def _load_locations(input_file: Path, lat_col: str, lon_col: str) -> list:
    """Load locations from CSV or JSON file."""
    locations = []

    if input_file.suffix.lower() == ".json":
        data = json.loads(input_file.read_text())
        if isinstance(data, list):
            for item in data:
                if lat_col in item and lon_col in item:
                    try:
                        lat = float(item[lat_col])
                        lon = float(item[lon_col])
                        locations.append((lat, lon))
                    except (ValueError, TypeError):
                        continue
    else:  # Assume CSV
        import csv

        with open(input_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if lat_col in row and lon_col in row:
                    try:
                        lat = float(row[lat_col])
                        lon = float(row[lon_col])
                        locations.append((lat, lon))
                    except (ValueError, TypeError):
                        continue

    return locations


def _output_csv(results, output_file: Path) -> None:
    """Output results to CSV format."""
    import csv

    # Prepare CSV data
    csv_data = []
    for result in results:
        row = {
            "latitude": result.latitude,
            "longitude": result.longitude,
            "provider": result.provider,
            "quality_score": result.quality_score,
            "distance_m": result.distance_m,
        }

        if result.observations:
            obs = result.observations[0]  # Use first observation
            row.update(
                {
                    "usda_classification": obs.classification_usda,
                    "wrb_classification": obs.classification_wrb,
                    "ph": obs.ph_h2o,
                    "texture_class": obs.texture_class,
                    "sand_percent": obs.sand_percent,
                    "silt_percent": obs.silt_percent,
                    "clay_percent": obs.clay_percent,
                    "organic_carbon": obs.organic_carbon,
                    "total_nitrogen": obs.total_nitrogen,
                    "bulk_density": obs.bulk_density,
                    "depth_cm": obs.depth_cm,
                }
            )

        csv_data.append(row)

    # Write CSV
    if csv_data:
        fieldnames = csv_data[0].keys()

        if output_file:
            with open(output_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            click.echo(f"CSV results written to {output_file}")
        else:
            import sys

            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)


if __name__ == "__main__":
    soil()
