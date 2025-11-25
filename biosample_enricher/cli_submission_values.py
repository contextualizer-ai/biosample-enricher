"""CLI for get_submission_values() - the primary API for NMDC metadata suggestions.

This CLI provides command-line access to the main biosample-enricher functionality:
retrieving NMDC submission-schema compliant values for geographic coordinates.

Examples:
    # Get climate and elevation data for San Francisco
    uv run biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt,annual_temp,elev

    # Get all supported slots
    uv run biosample-enricher get --lat 37.7749 --lon -122.4194 --slots all

    # Use median consensus strategy
    uv run biosample-enricher get --lat 37.7749 --lon -122.4194 --slots elev --strategy median

    # List available slots and providers
    uv run biosample-enricher info
"""

import json
import logging
import sys
from datetime import datetime

import click

from biosample_enricher.submission_values import (
    ALL_SUPPORTED_SLOTS,
    CLIMATE_PROVIDERS,
    CLIMATE_SLOTS,
    CONSENSUS_STRATEGIES,
    ELEVATION_PROVIDERS,
    ELEVATION_SLOTS,
    MARINE_SLOTS,
    SOIL_SLOTS,
    WEATHER_SLOTS,
    get_submission_values,
)

logger = logging.getLogger(__name__)


def _format_slot_status(slot: str) -> str:
    """Return status indicator for a slot."""
    # Based on current implementation status
    ready_slots = {"annual_precpt", "annual_temp", "elev"}
    caution_slots = {"temp", "ph", "depth"}

    if slot in ready_slots:
        return "ready"
    elif slot in caution_slots:
        return "caution"
    else:
        return "experimental"


@click.group()
def submission_values_cli() -> None:
    """Get NMDC submission-schema values for geographic coordinates.

    The primary API for biosample-enricher. Retrieves environmental metadata
    from authoritative data sources and returns it in NMDC submission format.

    \b
    Quick Start:
        biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt,elev
        biosample-enricher info

    \b
    For full documentation:
        https://microbiomedata.github.io/biosample-enricher/
    """


@submission_values_cli.command("get")
@click.option(
    "--lat",
    type=float,
    required=True,
    help="Latitude in decimal degrees (-90 to 90)",
)
@click.option(
    "--lon",
    type=float,
    required=True,
    help="Longitude in decimal degrees (-180 to 180)",
)
@click.option(
    "--slots",
    type=str,
    required=True,
    help='Comma-separated slot names, or "all" for all supported slots. '
    "Example: annual_precpt,annual_temp,elev",
)
@click.option(
    "--datetime",
    "datetime_str",
    type=str,
    default=None,
    help="Collection datetime for weather slots (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). "
    "Required for: temp, air_temp, humidity, wind_speed, wind_direction",
)
@click.option(
    "--providers",
    type=str,
    default=None,
    help="Comma-separated provider names to use (default: all available). "
    "Example: meteostat,nasa_power or usgs,open_topo_data",
)
@click.option(
    "--strategy",
    type=click.Choice(list(CONSENSUS_STRATEGIES)),
    default="mean",
    help="Consensus strategy for combining multi-provider values (default: mean)",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path for JSON results (default: stdout)",
)
@click.option(
    "--pretty/--compact",
    default=True,
    help="Pretty-print JSON output (default: pretty)",
)
@click.option(
    "--values-only",
    is_flag=True,
    default=False,
    help="Output only the values dict, not metadata",
)
def get_values(
    lat: float,
    lon: float,
    slots: str,
    datetime_str: str | None,
    providers: str | None,
    strategy: str,
    output: str | None,
    pretty: bool,
    values_only: bool,
) -> None:
    """Get submission-schema values for a location.

    \b
    Examples:
        # Basic usage - get climate and elevation
        biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt,annual_temp,elev

        # Get all supported slots
        biosample-enricher get --lat 37.7749 --lon -122.4194 --slots all

        # Weather data requires datetime
        biosample-enricher get --lat 37.7749 --lon -122.4194 --slots temp --datetime 2023-07-15

        # Use specific providers
        biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt --providers meteostat

        # Use median instead of mean
        biosample-enricher get --lat 37.7749 --lon -122.4194 --slots elev --strategy median

    \b
    Slot Categories:
        Climate (no datetime needed): annual_precpt, annual_temp
        Weather (datetime required): temp, air_temp, humidity, wind_speed, wind_direction
        Elevation: elev
        Marine: depth
        Soil: ph, soil_type
    """
    # Parse slots
    if slots.lower() == "all":
        slot_list = list(ALL_SUPPORTED_SLOTS)
    else:
        slot_list = [s.strip() for s in slots.split(",")]

    # Parse datetime if provided
    datetime_obj: datetime | None = None
    if datetime_str:
        try:
            # Try ISO format with time
            if "T" in datetime_str:
                datetime_obj = datetime.fromisoformat(datetime_str)
            else:
                # Date only
                datetime_obj = datetime.fromisoformat(datetime_str + "T00:00:00")
        except ValueError as e:
            raise click.BadParameter(
                f"Invalid datetime format: {datetime_str}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
            ) from e

    # Parse providers if provided
    provider_list: list[str] | None = None
    if providers:
        provider_list = [p.strip() for p in providers.split(",")]

    # Call the main function
    try:
        result = get_submission_values(
            lat=lat,
            lon=lon,
            slots=slot_list,
            datetime_obj=datetime_obj,
            providers=provider_list,
            strategy=strategy,
        )
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Format output
    output_data = result["values"] if values_only else result

    if pretty:
        json_str = json.dumps(output_data, indent=2, default=str)
    else:
        json_str = json.dumps(output_data, default=str)

    # Write output
    if output:
        with open(output, "w") as f:
            f.write(json_str)
        click.echo(f"Results written to {output}")
    else:
        click.echo(json_str)


@submission_values_cli.command("info")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
def show_info(output_format: str) -> None:
    """Show available slots, providers, and strategies.

    \b
    Examples:
        biosample-enricher info
        biosample-enricher info --format json
    """
    slots_info: dict[str, dict[str, list[str] | str]] = {
        "climate": {
            "names": sorted(CLIMATE_SLOTS),
            "description": "Multi-year climate averages (no datetime needed)",
            "providers": sorted(CLIMATE_PROVIDERS),
        },
        "weather": {
            "names": sorted(WEATHER_SLOTS),
            "description": "Point-in-time weather observations (datetime required)",
            "providers": ["meteostat", "open_meteo"],
        },
        "elevation": {
            "names": sorted(ELEVATION_SLOTS),
            "description": "Ground surface elevation",
            "providers": sorted(ELEVATION_PROVIDERS),
        },
        "marine": {
            "names": sorted(MARINE_SLOTS),
            "description": "Ocean/marine data",
            "providers": ["gebco", "noaa"],
        },
        "soil": {
            "names": sorted(SOIL_SLOTS),
            "description": "Soil properties",
            "providers": ["soilgrids", "usda_nrcs"],
        },
    }
    slot_status: dict[str, list[str]] = {
        "ready": ["annual_precpt", "annual_temp", "elev"],
        "caution": ["temp", "ph", "depth"],
        "experimental": sorted(
            s
            for s in ALL_SUPPORTED_SLOTS
            if s not in {"annual_precpt", "annual_temp", "elev", "temp", "ph", "depth"}
        ),
    }
    consensus_strategies: dict[str, str] = {
        "mean": "Arithmetic average across all providers (default, recommended)",
        "median": "Middle value - robust to outliers",
        "first": "Use first successful provider",
        "best_quality": "Use provider with best quality metric",
    }
    info = {
        "slots": slots_info,
        "all_slots": sorted(ALL_SUPPORTED_SLOTS),
        "consensus_strategies": consensus_strategies,
        "slot_status": slot_status,
    }

    if output_format == "json":
        click.echo(json.dumps(info, indent=2))
    else:
        click.echo("=" * 60)
        click.echo("BIOSAMPLE ENRICHER - Available Slots and Providers")
        click.echo("=" * 60)
        click.echo()

        click.echo("SUPPORTED SLOTS")
        click.echo("-" * 40)
        for category, data in slots_info.items():
            names = data["names"]
            description = data["description"]
            providers = data["providers"]
            click.echo(f"\n{category.upper()}:")
            if isinstance(names, list):
                click.echo(f"  Slots: {', '.join(names)}")
            click.echo(f"  Description: {description}")
            if isinstance(providers, list):
                click.echo(f"  Providers: {', '.join(providers)}")

        click.echo()
        click.echo("SLOT STATUS (reliability)")
        click.echo("-" * 40)
        click.echo(f"  Ready (production): {', '.join(slot_status['ready'])}")
        click.echo(f"  Caution (may have issues): {', '.join(slot_status['caution'])}")
        if slot_status["experimental"]:
            click.echo(f"  Experimental: {', '.join(slot_status['experimental'])}")

        click.echo()
        click.echo("CONSENSUS STRATEGIES")
        click.echo("-" * 40)
        for strategy, desc in consensus_strategies.items():
            click.echo(f"  {strategy}: {desc}")

        click.echo()
        click.echo("QUICK REFERENCE")
        click.echo("-" * 40)
        click.echo("  All slots: " + ", ".join(sorted(ALL_SUPPORTED_SLOTS)))
        click.echo()
        click.echo("EXAMPLES")
        click.echo("-" * 40)
        click.echo(
            "  biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt,elev"
        )
        click.echo("  biosample-enricher get --lat 37.7749 --lon -122.4194 --slots all")
        click.echo()


@submission_values_cli.command("slots")
def list_slots() -> None:
    """List all supported slot names (for scripting)."""
    for slot in sorted(ALL_SUPPORTED_SLOTS):
        click.echo(slot)


@submission_values_cli.command("providers")
@click.option(
    "--category",
    type=click.Choice(["climate", "elevation", "all"]),
    default="all",
    help="Filter by category",
)
def list_providers(category: str) -> None:
    """List available providers (for scripting)."""
    if category == "climate" or category == "all":
        for p in sorted(CLIMATE_PROVIDERS):
            click.echo(f"climate:{p}")
    if category == "elevation" or category == "all":
        for p in sorted(ELEVATION_PROVIDERS):
            click.echo(f"elevation:{p}")


@submission_values_cli.command("strategies")
def list_strategies() -> None:
    """List consensus strategies (for scripting)."""
    for s in sorted(CONSENSUS_STRATEGIES):
        click.echo(s)
