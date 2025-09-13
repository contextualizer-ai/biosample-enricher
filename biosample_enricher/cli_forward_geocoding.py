"""CLI interface for forward geocoding services (place names to coordinates)."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from biosample_enricher.forward_geocoding.service import ForwardGeocodingService
from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


@click.group()
def forward_geocoding():
    """Forward geocoding commands - convert place names to coordinates."""
    pass


@forward_geocoding.command()
@click.option(
    "--query", type=str, required=True, help="Place name or address to geocode"
)
@click.option(
    "--provider",
    type=click.Choice(["osm", "google", "auto"]),
    default="auto",
    help="Geocoding provider to use",
)
@click.option("--language", default="en", help="Language code for results")
@click.option(
    "--country", type=str, help="Country code to restrict search (e.g., 'US', 'CA')"
)
@click.option("--max-results", type=int, default=5, help="Maximum number of results")
@click.option("--output", type=click.Path(), help="Output file path (JSON)")
@click.option("--pretty", is_flag=True, help="Pretty print JSON output")
def lookup(
    query: str,
    provider: str,
    language: str,
    country: str | None,
    max_results: int,
    output: str | None,
    pretty: bool,
):
    """Look up coordinates for a place name."""
    service = ForwardGeocodingService()

    # Convert 'auto' to None for auto-selection
    provider_name = None if provider == "auto" else provider

    # Convert country to list if provided
    country_codes = [country.upper()] if country else None

    result = service.geocode(
        query,
        provider=provider_name,
        language=language,
        country_codes=country_codes,
        max_results=max_results,
    )

    if not result:
        click.echo("No results found", err=True)
        return

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


@forward_geocoding.command()
@click.option(
    "--query", type=str, required=True, help="Place name or address to geocode"
)
@click.option("--language", default="en", help="Language code for results")
@click.option(
    "--country", type=str, help="Country code to restrict search (e.g., 'US', 'CA')"
)
@click.option("--max-results", type=int, default=3, help="Maximum results per provider")
@click.option("--output", type=click.Path(), help="Output file path (JSON)")
@click.option("--pretty", is_flag=True, help="Pretty print JSON output")
def compare(
    query: str,
    language: str,
    country: str | None,
    max_results: int,
    output: str | None,
    pretty: bool,
):
    """Compare results from all available providers."""
    service = ForwardGeocodingService()

    # Convert country to list if provided
    country_codes = [country.upper()] if country else None

    results = service.geocode_multiple(
        query, language=language, country_codes=country_codes, max_results=max_results
    )

    if not results:
        click.echo("No results from any provider", err=True)
        return

    # Build comparison structure
    comparison: dict[str, Any] = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "providers": {},
        "summary": {},
    }

    # Add results from each provider
    for provider_name, result in results.items():
        comparison["providers"][provider_name] = result.model_dump(mode="json")

    # Add summary statistics
    comparison["summary"] = {
        "total_providers": len(service.get_available_providers()),
        "responding_providers": len(results),
        "total_locations": sum(len(r.locations) for r in results.values()),
        "providers_with_results": [name for name, r in results.items() if r.locations],
    }

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            if pretty:
                json.dump(comparison, f, indent=2, default=str)
            else:
                json.dump(comparison, f, default=str)

        click.echo(f"Comparison saved to {output_path}")
    else:
        if pretty:
            click.echo(json.dumps(comparison, indent=2, default=str))
        else:
            click.echo(json.dumps(comparison, default=str))


@forward_geocoding.command()
@click.option(
    "--query", type=str, required=True, help="Place name or address to geocode"
)
@click.option("--language", default="en", help="Language code for results")
@click.option("--country", type=str, help="Country code hint for better results")
def enrich(query: str, language: str, country: str | None):
    """Get coordinates and enrichment data for biosample place names."""
    service = ForwardGeocodingService()

    enrichment_data = service.get_coordinates_for_place(
        query, language=language, country_hint=country
    )

    if not enrichment_data:
        click.echo("No enrichment data available", err=True)
        return

    # Display enrichment data in a readable format
    click.echo(f"\nCoordinates for '{query}':")
    click.echo("=" * 60)

    # Primary coordinates (the main output)
    if "latitude" in enrichment_data and "longitude" in enrichment_data:
        click.echo(
            f"Coordinates: {enrichment_data['latitude']:.6f}, {enrichment_data['longitude']:.6f}"
        )
    else:
        click.echo("❌ No coordinates found")
        return

    # Formatted address
    if "formatted_address" in enrichment_data:
        click.echo(f"Address: {enrichment_data['formatted_address']}")

    # Administrative hierarchy
    admin_fields = ["country", "country_code", "state", "county", "city", "postal_code"]
    admin_data = {}
    for field in admin_fields:
        if field in enrichment_data:
            admin_data[field] = enrichment_data[field]

    if admin_data:
        click.echo("\nAdministrative hierarchy:")
        for field, value in admin_data.items():
            click.echo(f"  {field.replace('_', ' ').title()}: {value}")

    # Location context
    if "location_type" in enrichment_data:
        click.echo(f"\nLocation type: {enrichment_data['location_type']}")

    if "geometry_type" in enrichment_data:
        click.echo(f"Geometry type: {enrichment_data['geometry_type']}")

    # Quality metrics
    quality_fields = [
        "geocoding_confidence",
        "geocoding_relevance",
        "coordinate_accuracy_m",
    ]
    quality_data = {}
    for field in quality_fields:
        if field in enrichment_data:
            quality_data[field] = enrichment_data[field]

    if quality_data:
        click.echo("\nQuality metrics:")
        for field, value in quality_data.items():
            if field == "geocoding_confidence":
                click.echo(f"  Confidence: {value:.3f}")
            elif field == "geocoding_relevance":
                click.echo(f"  Relevance: {value:.3f}")
            elif field == "coordinate_accuracy_m":
                click.echo(f"  Accuracy: {value:.1f}m")

    # Provider information
    if "providers_attempted" in enrichment_data:
        attempted = enrichment_data["providers_attempted"]
        successful = enrichment_data.get("providers_successful", [])
        click.echo(f"\nProviders: {len(successful)}/{len(attempted)} successful")
        for provider in attempted:
            status = "✓" if provider in successful else "✗"
            click.echo(f"  {status} {provider}")

    # Error information if no success
    if not enrichment_data.get("providers_successful"):
        errors = enrichment_data.get("errors", [])
        if errors:
            click.echo("\nErrors:")
            for error in errors:
                click.echo(f"  • {error}")


@forward_geocoding.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True),
    required=True,
    help="Input file with place names (JSON or CSV)",
)
@click.option("--language", default="en", help="Language code for all lookups")
@click.option(
    "--output", type=click.Path(), required=True, help="Output file path (JSONL)"
)
@click.option("--batch-size", type=int, default=10, help="Batch processing size")
def batch(input_file: str, language: str, output: str, batch_size: int):
    """Process multiple place names from a file."""
    service = ForwardGeocodingService()

    # Load place names from input file
    input_path = Path(input_file)
    place_names = _load_place_names(input_path)

    if not place_names:
        click.echo("No valid place names found in input file", err=True)
        return

    click.echo(f"Processing {len(place_names)} place names...")

    # Process in batches
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for i in range(0, len(place_names), batch_size):
            batch_names = place_names[i : i + batch_size]

            for _j, place_name in enumerate(batch_names):
                try:
                    enrichment_data = service.get_coordinates_for_place(
                        place_name, language=language
                    )

                    # Add metadata
                    result_with_meta = {
                        "query": place_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "enrichment": enrichment_data,
                    }

                    f.write(json.dumps(result_with_meta, default=str) + "\n")

                except Exception as e:
                    logger.error(f"Failed to process '{place_name}': {e}")
                    # Write error record
                    error_record = {
                        "query": place_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": str(e),
                        "enrichment": {},
                    }
                    f.write(json.dumps(error_record, default=str) + "\n")

            click.echo(
                f"Processed batch {i // batch_size + 1}/{(len(place_names) - 1) // batch_size + 1}"
            )

    click.echo(f"Results saved to {output_path}")


@forward_geocoding.command()
def providers():
    """Show status of all forward geocoding providers."""
    service = ForwardGeocodingService()

    status = service.get_provider_status()

    click.echo("Forward Geocoding Provider Status:")
    click.echo("=" * 50)

    for _provider_key, info in status.items():
        available = info.get("available", False)
        status_icon = "✓" if available else "✗"

        click.echo(f"{status_icon} {info['name']}")

        if info.get("attribution"):
            click.echo(f"   Attribution: {info['attribution']}")

        if not available and "error" in info:
            click.echo(f"   Error: {info['error']}")

        click.echo()


@forward_geocoding.command()
@click.option("--query", type=str, default="New York City", help="Test place name")
def test(query: str):
    """Test forward geocoding with a sample place name."""
    click.echo(f"Testing forward geocoding for '{query}'")

    service = ForwardGeocodingService()

    try:
        # Test primary lookup
        result = service.geocode(query, max_results=3)

        if not result:
            click.echo("No results from primary lookup", err=True)
            return

        click.echo(f"\nPrimary result from {result.provider.name}:")
        click.echo(f"Status: {result.status}")
        click.echo(f"Locations found: {len(result.locations)}")

        if result.locations:
            primary = result.locations[0]
            click.echo(f"Address: {primary.formatted_address}")
            click.echo(f"Coordinates: {primary.latitude:.6f}, {primary.longitude:.6f}")
            if primary.country:
                click.echo(f"Country: {primary.country}")
            if primary.state:
                click.echo(f"State: {primary.state}")
            if primary.city:
                click.echo(f"City: {primary.city}")
            if primary.confidence:
                click.echo(f"Confidence: {primary.confidence:.3f}")
            if primary.relevance:
                click.echo(f"Relevance: {primary.relevance:.3f}")

        # Test enrichment
        click.echo("\nTesting enrichment...")
        enrichment_data = service.get_coordinates_for_place(query)

        if enrichment_data and "latitude" in enrichment_data:
            click.echo("✓ Enrichment successful")
            click.echo(
                f"Coordinates: {enrichment_data['latitude']:.6f}, {enrichment_data['longitude']:.6f}"
            )
            click.echo(
                f"Providers attempted: {enrichment_data.get('providers_attempted', [])}"
            )
            click.echo(
                f"Providers successful: {enrichment_data.get('providers_successful', [])}"
            )
        else:
            click.echo("✗ Enrichment failed")

    except Exception as e:
        click.echo(f"Error during test: {e}", err=True)


def _load_place_names(input_path: Path) -> list[str]:
    """Load place names from input file (JSON or CSV)."""
    place_names = []

    try:
        if input_path.suffix.lower() == ".json":
            with open(input_path) as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        place_names.append(item)
                    elif isinstance(item, dict):
                        # Look for common place name fields
                        for field in [
                            "place_name",
                            "location",
                            "address",
                            "geo_loc_name",
                        ]:
                            if field in item and item[field]:
                                place_names.append(str(item[field]))
                                break

        elif input_path.suffix.lower() == ".csv":
            import csv

            with open(input_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Look for common place name fields
                    for field in ["place_name", "location", "address", "geo_loc_name"]:
                        if field in row and row[field]:
                            place_names.append(row[field])
                            break

        else:
            click.echo(f"Unsupported file format: {input_path.suffix}", err=True)
            return []

    except Exception as e:
        click.echo(f"Error loading place names: {e}", err=True)
        return []

    return place_names
