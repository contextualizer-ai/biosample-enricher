#!/usr/bin/env python
"""
Comprehensive demonstration of all geocoding services.

Shows Google and OSM providers for both elevation and reverse geocoding.
"""

import json
import os
import sys
import time
from typing import Any, TypedDict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from biosample_enricher.elevation.providers.google import GoogleElevationProvider
from biosample_enricher.elevation.providers.osm import OSMElevationProvider
from biosample_enricher.logging_config import get_logger
from biosample_enricher.reverse_geocoding import (
    GoogleReverseGeocodingProvider,
    OSMReverseGeocodingProvider,
)

logger = get_logger(__name__)

console = Console()


class TestLocation(TypedDict):
    """Type definition for test locations."""

    name: str
    lat: float
    lon: float


# Test locations
TEST_LOCATIONS: list[TestLocation] = [
    {"name": "Googleplex, Mountain View", "lat": 37.4224, "lon": -122.0856},
    {"name": "Mount Everest Base Camp", "lat": 28.0026, "lon": 86.8528},
    {"name": "Death Valley", "lat": 36.5323, "lon": -116.9325},
    {"name": "Tokyo Tower", "lat": 35.6586, "lon": 139.7454},
    {"name": "Pacific Ocean", "lat": 30.0, "lon": -140.0},
]


def test_google_apis(lat: float, lon: float, name: str) -> dict[str, Any]:
    """Test Google APIs for a location."""
    results = {"name": name, "lat": lat, "lon": lon}

    # Test Google Elevation
    try:
        console.print("  [cyan]Google Elevation[/cyan]...", end="")
        elevation_provider = GoogleElevationProvider()
        elev_result = elevation_provider.fetch(lat, lon, read_from_cache=False)

        if elev_result.ok:
            results["google_elevation"] = {
                "elevation_m": elev_result.elevation,
                "resolution_m": elev_result.resolution_m,
                "status": "success",
            }
            console.print(f" ✓ {elev_result.elevation:.2f}m", style="green")
        else:
            results["google_elevation"] = {
                "status": "failed",
                "error": elev_result.error,
            }
            console.print(f" ✗ {elev_result.error}", style="red")
    except Exception as e:
        results["google_elevation"] = {"status": "error", "error": str(e)}
        console.print(f" ✗ Error: {e}", style="red")

    # Test Google Reverse Geocoding
    try:
        console.print("  [cyan]Google Geocoding[/cyan]...", end="")
        geocoding_provider = GoogleReverseGeocodingProvider()
        geo_result = geocoding_provider.fetch(lat, lon, read_from_cache=False, limit=3)

        if geo_result.ok and geo_result.result:
            best = geo_result.result.get_best_match()
            if best:
                results["google_geocoding"] = {
                    "address": best.formatted_address,
                    "country": best.country,
                    "state": best.state,
                    "city": best.city,
                    "status": "success",
                }
                console.print(f" ✓ {best.country or 'Unknown'}", style="green")
            else:
                results["google_geocoding"] = {"status": "no_results"}
                console.print(" ⚠ No results", style="yellow")
        else:
            results["google_geocoding"] = {
                "status": "failed",
                "error": geo_result.error,
            }
            console.print(f" ✗ {geo_result.error}", style="red")
    except Exception as e:
        results["google_geocoding"] = {"status": "error", "error": str(e)}
        console.print(f" ✗ Error: {e}", style="red")

    return results


def test_osm_apis(lat: float, lon: float, name: str) -> dict[str, Any]:
    """Test OSM APIs for a location."""
    results = {"name": name, "lat": lat, "lon": lon}

    # Test OSM Elevation
    try:
        console.print("  [cyan]OSM Elevation[/cyan]...", end="")
        elevation_provider = OSMElevationProvider()
        elev_result = elevation_provider.fetch(lat, lon, read_from_cache=False)

        if elev_result.ok:
            results["osm_elevation"] = {
                "elevation_m": elev_result.elevation,
                "resolution_m": elev_result.resolution_m,
                "status": "success",
            }
            console.print(f" ✓ {elev_result.elevation:.2f}m", style="green")
        else:
            results["osm_elevation"] = {"status": "failed", "error": elev_result.error}
            console.print(f" ✗ {elev_result.error}", style="red")
    except Exception as e:
        results["osm_elevation"] = {"status": "error", "error": str(e)}
        console.print(f" ✗ Error: {e}", style="red")

    # Test OSM Reverse Geocoding
    try:
        console.print("  [cyan]OSM Geocoding[/cyan]...", end="")
        geocoding_provider = OSMReverseGeocodingProvider()
        geo_result = geocoding_provider.fetch(lat, lon, read_from_cache=False, limit=3)

        if geo_result.ok and geo_result.result:
            best = geo_result.result.get_best_match()
            if best:
                results["osm_geocoding"] = {
                    "address": best.formatted_address,
                    "country": best.country,
                    "state": best.state,
                    "city": best.city,
                    "status": "success",
                }
                console.print(f" ✓ {best.country or 'Unknown'}", style="green")
            else:
                results["osm_geocoding"] = {"status": "no_results"}
                console.print(" ⚠ No results", style="yellow")
        else:
            results["osm_geocoding"] = {"status": "failed", "error": geo_result.error}
            console.print(f" ✗ {geo_result.error}", style="red")
    except Exception as e:
        results["osm_geocoding"] = {"status": "error", "error": str(e)}
        console.print(f" ✗ Error: {e}", style="red")

    # Rate limiting for OSM
    time.sleep(1.0)

    return results


def display_results_table(all_results: list[dict[str, Any]]) -> None:
    """Display results in a formatted table."""
    console.print("\n[bold]Summary Table:[/bold]")

    # Elevation table
    table = Table(show_header=True, header_style="bold blue", title="Elevation Results")
    table.add_column("Location", style="cyan")
    table.add_column("Google (m)", justify="right")
    table.add_column("OSM (m)", justify="right")
    table.add_column("Difference (m)", justify="right")

    for result in all_results:
        google_elev = result.get("google_elevation", {})
        osm_elev = result.get("osm_elevation", {})

        google_val = google_elev.get("elevation_m", "N/A")
        osm_val = osm_elev.get("elevation_m", "N/A")

        google_str = (
            f"{google_val:.2f}"
            if isinstance(google_val, int | float)
            else str(google_val)
        )
        osm_str = f"{osm_val:.2f}" if isinstance(osm_val, int | float) else str(osm_val)

        diff_str = "-"
        if isinstance(google_val, int | float) and isinstance(osm_val, int | float):
            diff = abs(google_val - osm_val)
            diff_str = f"{diff:.2f}"

        table.add_row(result["name"], google_str, osm_str, diff_str)

    console.print(table)

    # Geocoding table
    table = Table(show_header=True, header_style="bold blue", title="Geocoding Results")
    table.add_column("Location", style="cyan")
    table.add_column("Google Country", justify="left")
    table.add_column("OSM Country", justify="left")
    table.add_column("Match", justify="center")

    for result in all_results:
        google_geo = result.get("google_geocoding", {})
        osm_geo = result.get("osm_geocoding", {})

        google_country = google_geo.get("country", "N/A")
        osm_country = osm_geo.get("country", "N/A")

        match = (
            "✓" if google_country == osm_country and google_country != "N/A" else "✗"
        )
        match_style = "green" if match == "✓" else "red"

        table.add_row(
            result["name"],
            google_country,
            osm_country,
            f"[{match_style}]{match}[/{match_style}]",
        )

    console.print(table)


def main() -> None:
    """Main entry point."""
    console.print(
        Panel.fit(
            "[bold green]Geocoding Services Comprehensive Demo[/bold green]\n"
            "Testing Google and OSM providers for Elevation and Reverse Geocoding",
            border_style="green",
        )
    )

    # Check for Google API key
    if os.getenv("GOOGLE_MAIN_API_KEY"):
        console.print("[green]✓ Google API key found[/green]")
    else:
        console.print("[red]✗ Google API key not found - Google tests will fail[/red]")
        console.print(
            "Set GOOGLE_MAIN_API_KEY environment variable to enable Google APIs"
        )

    all_results = []

    for location in TEST_LOCATIONS:
        console.print(f"\n[bold yellow]Testing: {location['name']}[/bold yellow]")
        console.print(f"Coordinates: {location['lat']:.4f}, {location['lon']:.4f}")

        # Test Google APIs
        console.print("[bold]Google APIs:[/bold]")
        google_results = test_google_apis(
            location["lat"], location["lon"], location["name"]
        )

        # Test OSM APIs
        console.print("[bold]OSM APIs:[/bold]")
        osm_results = test_osm_apis(location["lat"], location["lon"], location["name"])

        # Combine results
        combined = {**google_results, **osm_results}
        all_results.append(combined)

        # Brief pause between locations
        time.sleep(0.5)

    # Display summary
    display_results_table(all_results)

    # Save results to JSON
    output_file = "geocoding_demo_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    console.print(f"\n[green]Results saved to {output_file}[/green]")

    console.print("\n[bold green]Demo completed successfully![/bold green]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise
