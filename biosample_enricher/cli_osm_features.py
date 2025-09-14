"""CLI interface for OpenStreetMap geographic features enrichment."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from biosample_enricher.logging_config import get_logger
from biosample_enricher.osm_features.service import OSMFeaturesService

logger = get_logger(__name__)


@click.group()
def osm_features():
    """OpenStreetMap geographic features commands."""
    pass


@osm_features.command()
@click.option("--latitude", type=float, required=True, help="Latitude coordinate")
@click.option("--longitude", type=float, required=True, help="Longitude coordinate")
@click.option(
    "--radius", type=int, default=1000, help="Search radius in meters (1-50000)"
)
@click.option(
    "--providers",
    type=click.Choice(["osm", "google", "both"]),
    default="both",
    help="Which providers to use for geographic features",
)
@click.option("--timeout", type=int, default=180, help="Query timeout in seconds")
@click.option("--output", type=click.Path(), help="Output file path (JSON)")
@click.option("--pretty", is_flag=True, help="Pretty print JSON output")
def lookup(
    latitude: float,
    longitude: float,
    radius: int,
    providers: str,
    timeout: int,
    output: str | None,
    pretty: bool,
):
    """Look up geographic features around coordinates."""
    service = OSMFeaturesService()

    click.echo(
        f"Getting geographic features for {latitude}, {longitude} within {radius}m using {providers} provider(s)..."
    )

    result_dict: dict[str, Any] = {}

    if providers == "both":
        combined_result = service.get_combined_features_for_location(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius,
            timeout_s=timeout,
        )
        result_dict = combined_result.model_dump(mode="json")
    elif providers == "osm":
        osm_result = service.get_features_for_location(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius,
            timeout_s=timeout,
        )
        if not osm_result:
            click.echo("No OSM features found or API error", err=True)
            return
        result_dict = osm_result.model_dump(mode="json")
    elif providers == "google":
        if not service.google_provider:
            click.echo("Google Places provider not available", err=True)
            return

        google_fetch = service.google_provider.get_features(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius,
            timeout_s=timeout,
        )
        if not google_fetch.ok:
            click.echo(f"Google Places API error: {google_fetch.error}", err=True)
            return

        result_dict = (
            google_fetch.result.model_dump(mode="json") if google_fetch.result else {}
        )
    else:
        click.echo(f"Unknown provider: {providers}", err=True)
        return

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


@osm_features.command()
@click.option("--latitude", type=float, required=True, help="Latitude coordinate")
@click.option("--longitude", type=float, required=True, help="Longitude coordinate")
@click.option("--radius", type=int, default=1000, help="Search radius in meters")
@click.option("--timeout", type=int, default=180, help="Query timeout in seconds")
@click.option(
    "--providers",
    type=click.Choice(["osm", "google", "both"]),
    default="both",
    help="Which providers to use for geographic features",
)
def enrich(
    latitude: float, longitude: float, radius: int, timeout: int, providers: str
):
    """Get enrichment data for biosample coordinates."""
    service = OSMFeaturesService()

    use_combined = providers == "both"
    if providers == "google" and not service.google_provider:
        click.echo("❌ Google Places provider not available", err=True)
        return

    enrichment_data = service.enrich_biosample_location(
        latitude=latitude,
        longitude=longitude,
        radius_m=radius,
        timeout_s=timeout,
        use_combined=use_combined,
    )

    # Check for successful enrichment
    if use_combined:
        success = enrichment_data.get("features_enrichment_success", False)
        if not success:
            click.echo("❌ All geographic feature providers failed", err=True)
            if "features_error" in enrichment_data:
                click.echo(f"Error: {enrichment_data['features_error']}", err=True)
            return

        # Display combined enrichment data
        click.echo(f"\\n🗺️  Geographic Features for {latitude}, {longitude}:")
        click.echo("=" * 60)

        # Show provider status
        providers_successful = enrichment_data.get("features_providers_successful", [])
        providers_failed = enrichment_data.get("features_providers_failed", [])
        click.echo(
            f"Successful providers: {', '.join(providers_successful) if providers_successful else 'None'}"
        )
        if providers_failed:
            click.echo(f"Failed providers: {', '.join(providers_failed)}")

        # Combined statistics
        osm_features = enrichment_data.get("osm_features_found", 0)
        google_features = enrichment_data.get("google_places_found", 0)
        total_combined = enrichment_data.get("features_total_named_combined", 0)

        click.echo("\\nFeature counts:")
        if osm_features > 0:
            click.echo(f"  OSM named features: {osm_features}")
        if google_features > 0:
            click.echo(f"  Google Places: {google_features}")
        click.echo(f"  Total combined: {total_combined}")

        radius = enrichment_data.get("features_query_radius_m", radius)
        click.echo(f"Query radius: {radius}m")

    else:
        # Legacy OSM-only display
        if not enrichment_data.get("osm_enrichment_success"):
            click.echo("❌ OSM enrichment failed", err=True)
            if "osm_error" in enrichment_data:
                click.echo(f"Error: {enrichment_data['osm_error']}", err=True)
            return

        # Display enrichment data in a readable format
        click.echo(f"\\n🗺️  OSM Features for {latitude}, {longitude}:")
        click.echo("=" * 60)

        # Basic statistics
        features_found = enrichment_data.get("osm_features_found", 0)
        categories_found = enrichment_data.get("osm_categories_found", 0)
        total_elements = enrichment_data.get("osm_total_elements", 0)

        click.echo(
            f"Features found: {features_found} named, {categories_found} categories"
        )
        click.echo(f"Total OSM elements: {total_elements}")
        click.echo(
            f"Query radius: {enrichment_data.get('osm_query_radius_m', 'unknown')}m"
        )

    # Nearest features by category
    click.echo("\\nNearest features by category:")
    feature_categories = ["natural", "waterway", "highway", "amenity", "building"]

    for category in feature_categories:
        name_key = f"nearest_{category}_name"
        type_key = f"nearest_{category}_type"
        distance_key = f"nearest_{category}_distance_km"

        if name_key in enrichment_data and enrichment_data[name_key]:
            name = enrichment_data[name_key]
            feature_type = enrichment_data.get(type_key, "unknown")
            distance = enrichment_data.get(distance_key)

            if distance is not None:
                click.echo(
                    f"  {category.title()}: {name} ({feature_type}) - {distance:.3f}km"
                )
            else:
                click.echo(f"  {category.title()}: {name} ({feature_type})")
        else:
            click.echo(f"  {category.title()}: None found")

    # Distance summaries
    click.echo("\\nDistance summaries:")
    for category in feature_categories:
        within_1km_key = f"{category}_within_1km"
        avg_distance_key = f"avg_{category}_km"

        within_1km = enrichment_data.get(within_1km_key, 0)
        avg_distance = enrichment_data.get(avg_distance_key)

        if within_1km > 0:
            if avg_distance:
                click.echo(
                    f"  {category.title()}: {within_1km} within 1km, avg distance: {avg_distance:.3f}km"
                )
            else:
                click.echo(f"  {category.title()}: {within_1km} within 1km")

    # Feature counts by category
    click.echo("\\nFeature counts by OSM tag:")
    osm_tags = [
        k for k in enrichment_data if k.startswith("osm_") and k.endswith("_count")
    ]

    if osm_tags:
        for tag_key in sorted(osm_tags):
            tag_name = tag_key[4:-6]  # Remove 'osm_' prefix and '_count' suffix
            count = enrichment_data[tag_key]
            if count > 0:
                click.echo(f"  {tag_name}: {count}")
    else:
        click.echo("  No categorized features found")


@osm_features.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True),
    required=True,
    help="Input file with coordinates (JSON or CSV)",
)
@click.option("--radius", type=int, default=1000, help="Search radius in meters")
@click.option(
    "--timeout", type=int, default=180, help="Query timeout in seconds per location"
)
@click.option(
    "--output", type=click.Path(), required=True, help="Output file path (JSONL)"
)
@click.option("--batch-size", type=int, default=10, help="Batch processing size")
def batch(input_file: str, radius: int, timeout: int, output: str, batch_size: int):
    """Process multiple locations from a file."""
    service = OSMFeaturesService()

    # Load coordinates from input file
    input_path = Path(input_file)
    coordinates = _load_coordinates(input_path)

    if not coordinates:
        click.echo("No valid coordinates found in input file", err=True)
        return

    click.echo(f"Processing {len(coordinates)} locations...")

    # Process in batches
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for i in range(0, len(coordinates), batch_size):
            batch_coords = coordinates[i : i + batch_size]

            for _j, (lat, lon) in enumerate(batch_coords):
                try:
                    enrichment_data = service.enrich_biosample_location(
                        latitude=lat,
                        longitude=lon,
                        radius_m=radius,
                        timeout_s=timeout,
                    )

                    # Add metadata
                    result_with_meta = {
                        "coordinates": {"latitude": lat, "longitude": lon},
                        "timestamp": datetime.utcnow().isoformat(),
                        "enrichment": enrichment_data,
                    }

                    f.write(json.dumps(result_with_meta, default=str) + "\\n")

                except Exception as e:
                    logger.error(f"Failed to process {lat}, {lon}: {e}")
                    # Write error record
                    error_record = {
                        "coordinates": {"latitude": lat, "longitude": lon},
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": str(e),
                        "enrichment": {},
                    }
                    f.write(json.dumps(error_record, default=str) + "\\n")

            click.echo(
                f"Processed batch {i // batch_size + 1}/{(len(coordinates) - 1) // batch_size + 1}"
            )

    click.echo(f"Results saved to {output_path}")


@osm_features.command()
def providers():
    """Show status of OSM features providers."""
    service = OSMFeaturesService()

    status = service.get_provider_status()

    click.echo("OSM Features Provider Status:")
    click.echo("=" * 50)

    for _provider_key, info in status.items():
        available = info.get("available", False)
        status_icon = "✓" if available else "✗"

        click.echo(f"{status_icon} {info['name']}")

        if info.get("attribution"):
            click.echo(f"   Attribution: {info['attribution']}")

        if info.get("base_url"):
            click.echo(f"   Endpoint: {info['base_url']}")

        if info.get("rate_limit"):
            click.echo(f"   Rate limit: {info['rate_limit']}")

        if not available and "error" in info:
            click.echo(f"   Error: {info['error']}")

        click.echo()


@osm_features.command()
@click.option(
    "--latitude", type=float, default=40.7589, help="Test latitude (default: NYC)"
)
@click.option(
    "--longitude", type=float, default=-73.9851, help="Test longitude (default: NYC)"
)
@click.option("--radius", type=int, default=500, help="Test radius in meters")
def test(latitude: float, longitude: float, radius: int):
    """Test OSM features enrichment with sample coordinates."""
    click.echo(f"Testing OSM features for {latitude}, {longitude} within {radius}m")

    service = OSMFeaturesService()

    try:
        # Test provider status
        status = service.get_provider_status()
        provider_available = any(
            info.get("available", False) for info in status.values()
        )

        if not provider_available:
            click.echo("❌ OSM provider not available", err=True)
            return

        click.echo("✓ OSM provider available")

        # Test feature lookup
        result = service.get_features_for_location(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius,
            timeout_s=60,
        )

        if not result:
            click.echo("❌ No results from OSM lookup", err=True)
            return

        click.echo("\\n📊 Results Summary:")
        click.echo(f"Named features: {result.named_features_count}")
        click.echo(f"Unnamed categories: {result.unnamed_categories_count}")
        click.echo(f"Total elements: {result.total_elements}")
        click.echo(f"Success: {result.success}")

        if result.named_features:
            click.echo("\\n🏆 Nearest named features:")
            for i, feature in enumerate(result.named_features[:5]):
                click.echo(
                    f"  {i + 1}. {feature.name} ({feature.category.value}/{feature.subcategory}) "
                    f"- {feature.distance_km:.3f}km"
                )

        if result.unnamed_counts:
            click.echo("\\n📈 Top unnamed categories:")
            sorted_categories = sorted(
                result.unnamed_counts, key=lambda x: x.total_count, reverse=True
            )
            for cat in sorted_categories[:5]:
                click.echo(f"  {cat.key}: {cat.total_count} features")

        # Test enrichment
        click.echo("\\n🧪 Testing enrichment format...")
        enrichment = service.enrich_biosample_location(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius,
        )

        if enrichment.get("osm_enrichment_success"):
            click.echo("✓ Enrichment successful")
            key_fields = [
                "osm_features_found",
                "osm_categories_found",
                "nearest_natural_name",
                "nearest_highway_name",
            ]
            for field in key_fields:
                if field in enrichment:
                    click.echo(f"  {field}: {enrichment[field]}")
        else:
            click.echo("❌ Enrichment failed")

    except Exception as e:
        click.echo(f"Error during test: {e}", err=True)


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
                    coords = _extract_coordinates_from_item(item)
                    if coords:
                        coordinates.append(coords)

        elif input_path.suffix.lower() == ".csv":
            import csv

            with open(input_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    coords = _extract_coordinates_from_item(row)
                    if coords:
                        coordinates.append(coords)

        else:
            click.echo(f"Unsupported file format: {input_path.suffix}", err=True)
            return []

    except Exception as e:
        click.echo(f"Error loading coordinates: {e}", err=True)
        return []

    return coordinates


def _extract_coordinates_from_item(item: Any) -> tuple[float, float] | None:
    """Extract coordinates from a data item."""
    if isinstance(item, list | tuple) and len(item) >= 2:
        try:
            lat = float(item[0])
            lon = float(item[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        except (ValueError, TypeError):
            pass

    elif isinstance(item, dict):
        # Try various coordinate field patterns
        coord_patterns = [
            ("latitude", "longitude"),
            ("lat", "lon"),
            ("lat", "lng"),
            ("y", "x"),
        ]

        for lat_field, lon_field in coord_patterns:
            if lat_field in item and lon_field in item:
                try:
                    lat = float(item[lat_field])
                    lon = float(item[lon_field])
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return lat, lon
                except (ValueError, TypeError):
                    continue

    return None
