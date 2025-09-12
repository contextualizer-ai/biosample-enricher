#!/usr/bin/env python3
"""
Weather enrichment CLI for biosample environmental context.

Command-line interface for day-specific weather data enrichment with
multiple providers, schema mapping, and coverage metrics.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import click

from biosample_enricher.logging_config import get_logger
from biosample_enricher.weather import (
    MeteostatProvider,
    OpenMeteoProvider,
    WeatherService,
)
from biosample_enricher.weather.metrics import WeatherEnrichmentMetrics

if TYPE_CHECKING:
    from biosample_enricher.weather.providers.base import WeatherProviderBase

logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def weather_cli(debug: bool):
    """Weather enrichment CLI for biosample environmental context."""
    if debug:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)


@weather_cli.command()
@click.option("--lat", type=float, required=True, help="Latitude in decimal degrees")
@click.option("--lon", type=float, required=True, help="Longitude in decimal degrees")
@click.option("--date", type=str, required=True, help="Date in YYYY-MM-DD format")
@click.option(
    "--providers",
    type=str,
    default="open_meteo,meteostat",
    help="Comma-separated provider list",
)
@click.option("--output", type=click.Path(), help="Output file path (JSON)")
@click.option(
    "--schema",
    type=click.Choice(["nmdc", "gold"]),
    default="nmdc",
    help="Target schema for mapping",
)
def lookup(
    lat: float,
    lon: float,
    date: str,
    providers: str,
    output: str | None,
    schema: str,
):
    """Get weather data for specific coordinates and date."""

    try:
        # Parse date (validate format)
        datetime.strptime(date, "%Y-%m-%d").date()

        # Initialize providers
        provider_list: list[WeatherProviderBase] = []
        for provider_name in providers.split(","):
            provider_name = provider_name.strip().lower()
            if provider_name == "open_meteo":
                provider_list.append(OpenMeteoProvider())
            elif provider_name == "meteostat":
                provider_list.append(MeteostatProvider())
            else:
                click.echo(f"Unknown provider: {provider_name}", err=True)
                return 1

        # Create weather service
        weather_service = WeatherService(providers=provider_list)

        # Create mock biosample for enrichment
        if schema == "nmdc":
            biosample = {
                "id": f"demo:weather-lookup-{lat}-{lon}",
                "lat_lon": {"latitude": lat, "longitude": lon},
                "collection_date": {"has_raw_value": date},
            }
        else:  # gold
            biosample = {
                "id": f"demo-weather-lookup-{lat}-{lon}",
                "latitude": lat,  # type: ignore[dict-item]
                "longitude": lon,  # type: ignore[dict-item]
                "dateCollected": date,
            }

        # Perform weather enrichment
        click.echo(f"Getting weather for ({lat}, {lon}) on {date}...")
        result = weather_service.get_weather_for_biosample(
            biosample, target_schema=schema
        )

        if result["enrichment_success"]:
            click.echo("✅ Weather enrichment successful!")

            weather_result = result["weather_result"]
            coverage_metrics = result["coverage_metrics"]

            # Display results
            click.echo("\n🌤️  Weather Summary:")
            click.echo(f"Temporal quality: {weather_result.overall_quality.value}")
            click.echo(
                f"Successful providers: {', '.join(weather_result.successful_providers)}"
            )
            click.echo(
                f"Fields enriched: {coverage_metrics['enriched_count']}/{coverage_metrics['total_possible_fields']}"
            )
            click.echo(
                f"Quality score: {coverage_metrics['average_quality_score']:.0f}/100"
            )

            # Display weather parameters
            if weather_result.temperature:
                temp_val = weather_result.temperature.value
                if isinstance(temp_val, dict):
                    click.echo(
                        f"\n🌡️  Temperature: {temp_val['avg']:.1f}°C (range: {temp_val['min']:.1f}-{temp_val['max']:.1f}°C)"
                    )
                else:
                    click.echo(f"\n🌡️  Temperature: {temp_val:.1f}°C")

            if weather_result.wind_speed:
                wind_val = weather_result.wind_speed.value
                wind_speed = wind_val["avg"] if isinstance(wind_val, dict) else wind_val
                click.echo(
                    f"💨 Wind: {wind_speed:.1f} {weather_result.wind_speed.unit}"
                )

            if weather_result.humidity:
                click.echo(f"💧 Humidity: {weather_result.humidity.value:.1f}%")

            if weather_result.precipitation:
                click.echo(
                    f"🌧️  Precipitation: {weather_result.precipitation.value:.1f} mm"
                )

            if weather_result.solar_radiation:
                click.echo(
                    f"☀️  Solar radiation: {weather_result.solar_radiation.value:.1f} W/m²"
                )

            # Display schema mapping
            click.echo(f"\n📋 {schema.upper()} Schema Mapping:")
            schema_mapping = result["schema_mapping"]
            for field_name, field_data in schema_mapping.items():
                if isinstance(field_data, dict):
                    if "has_numeric_value" in field_data:
                        click.echo(
                            f"  {field_name}: {field_data['has_numeric_value']} {field_data.get('has_unit', '')}"
                        )
                    elif "has_raw_value" in field_data:
                        click.echo(f"  {field_name}: {field_data['has_raw_value']}")
                else:
                    click.echo(f"  {field_name}: {field_data}")

            # Save output if requested
            if output:
                output_data = {
                    "weather_result": result["weather_result"].dict(),
                    "schema_mapping": result["schema_mapping"],
                    "coverage_metrics": result["coverage_metrics"],
                }

                Path(output).write_text(json.dumps(output_data, indent=2, default=str))
                click.echo(f"\n💾 Results saved to {output}")

        else:
            click.echo("❌ Weather enrichment failed")
            if "error" in result:
                click.echo(f"Error: {result['error']}")
            return 1

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        return 1


@weather_cli.command()
@click.option(
    "--input-file",
    type=click.Path(exists=True),
    required=True,
    help="Input biosamples JSON file",
)
@click.option(
    "--source", type=str, required=True, help="Source identifier (nmdc, gold, etc.)"
)
@click.option(
    "--output-dir", type=click.Path(), help="Output directory for metrics files"
)
@click.option("--sample-limit", type=int, help="Limit number of samples to process")
def analyze(
    input_file: str, source: str, output_dir: str | None, sample_limit: int | None
):
    """Analyze weather enrichment coverage for a collection of biosamples."""

    try:
        # Load biosamples
        with open(input_file) as f:
            biosamples = json.load(f)

        if not isinstance(biosamples, list):
            click.echo("Input file must contain a list of biosamples", err=True)
            return 1

        # Apply sample limit if specified
        if sample_limit:
            biosamples = biosamples[:sample_limit]
            click.echo(f"Limited to {len(biosamples)} samples")

        click.echo(
            f"Analyzing weather coverage for {len(biosamples)} {source} biosamples..."
        )

        # Initialize metrics analyzer
        metrics_analyzer = WeatherEnrichmentMetrics()

        # Perform analysis
        analysis = metrics_analyzer.analyze_biosample_collection(biosamples, source)

        # Display results
        click.echo("\n📊 Coverage Analysis Results:")
        click.echo(f"Source: {analysis['source'].upper()}")
        click.echo(f"Samples analyzed: {analysis['sample_count']}")

        click.echo("\n📈 Before → After Coverage:")
        improvements = analysis["improvements"]
        for weather_param, improvement_data in improvements.items():
            before = improvement_data["before_coverage"]
            after = improvement_data["after_coverage"]
            delta = improvement_data["absolute_improvement"]
            category = improvement_data["improvement_category"]

            click.echo(
                f"  {weather_param}: {before:.1f}% → {after:.1f}% (+{delta:.1f}%) [{category}]"
            )

        # Show enrichment summary
        enrichment_summary = analysis["enrichment_summary"]
        if "enriched_samples" in enrichment_summary:
            click.echo(
                f"\n✅ Successfully enriched: {enrichment_summary['enriched_samples']} samples"
            )

            if "average_quality_score" in enrichment_summary:
                click.echo(
                    f"Average quality score: {enrichment_summary['average_quality_score']:.0f}/100"
                )

        # Save output files if directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save detailed analysis
            analysis_file = output_path / f"{source}_weather_analysis.json"
            with open(analysis_file, "w") as f:
                json.dump(analysis, f, indent=2, default=str)
            click.echo(f"\n💾 Analysis saved to {analysis_file}")

            # Save metrics report
            report_df = metrics_analyzer.generate_metrics_report([analysis])
            report_file = output_path / f"{source}_weather_metrics.csv"
            report_df.to_csv(report_file, index=False)
            click.echo(f"📋 Metrics report saved to {report_file}")

            # Save detailed enrichment results
            detailed_file = output_path / f"{source}_weather_detailed.csv"
            metrics_analyzer.export_detailed_results(str(detailed_file))
            click.echo(f"🔬 Detailed results saved to {detailed_file}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        return 1


@weather_cli.command()
def demo():
    """Run weather enrichment demonstration."""

    click.echo("🌤️  Weather Enrichment Demo")
    click.echo("=" * 50)

    # Sample coordinates and dates
    test_cases = [
        {
            "name": "Kellogg Biological Station, Michigan",
            "lat": 42.5,
            "lon": -85.4,
            "date": "2018-07-12",
        },
        {
            "name": "Central California",
            "lat": 36.7783,
            "lon": -119.4179,
            "date": "2019-08-15",
        },
        {
            "name": "Seattle, Washington",
            "lat": 47.6062,
            "lon": -122.3321,
            "date": "2020-03-20",
        },
    ]

    weather_service = WeatherService()

    for i, test_case in enumerate(test_cases, 1):
        click.echo(f"\n📍 Test {i}: {test_case['name']}")
        click.echo(f"Location: {test_case['lat']}, {test_case['lon']}")
        click.echo(f"Date: {test_case['date']}")

        # Create sample biosample
        biosample = {
            "id": f"demo:test-{i}",
            "lat_lon": {"latitude": test_case["lat"], "longitude": test_case["lon"]},
            "collection_date": {"has_raw_value": test_case["date"]},
        }

        try:
            result = weather_service.get_weather_for_biosample(biosample)

            if result["enrichment_success"]:
                weather_result = result["weather_result"]
                coverage = result["coverage_metrics"]

                click.echo(
                    f"✅ Success - Quality: {weather_result.overall_quality.value}"
                )
                click.echo(
                    f"Providers: {', '.join(weather_result.successful_providers)}"
                )
                click.echo(f"Enriched fields: {coverage['enriched_count']}")

                if weather_result.temperature:
                    temp_val = weather_result.temperature.value
                    if isinstance(temp_val, dict):
                        click.echo(f"Temperature: {temp_val['avg']:.1f}°C")
                    else:
                        click.echo(f"Temperature: {temp_val:.1f}°C")
            else:
                click.echo("❌ Enrichment failed")

        except Exception as e:
            click.echo(f"❌ Error: {e}")

    click.echo("\n✅ Demo completed!")


if __name__ == "__main__":
    weather_cli()
