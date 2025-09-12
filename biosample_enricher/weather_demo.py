#!/usr/bin/env python3
"""
Weather enrichment demonstration for biosample environmental context.

Shows day-specific weather enrichment using multiple providers with
before/after coverage metrics for NMDC and GOLD biosample schemas.
"""

from datetime import date
from typing import Any

from biosample_enricher.logging_config import get_logger
from biosample_enricher.weather import (
    MeteostatProvider,
    OpenMeteoProvider,
    WeatherService,
)
from biosample_enricher.weather.metrics import WeatherEnrichmentMetrics

logger = get_logger(__name__)


def create_sample_biosamples() -> dict[str, list[dict[str, Any]]]:
    """Create sample biosamples for demonstration."""

    nmdc_samples = [
        {
            "id": "nmdc:bsm-11-demo001",
            "lat_lon": {"latitude": 42.5, "longitude": -85.4},
            "collection_date": {"has_raw_value": "2018-07-12T14:30Z"},
            "env_broad_scale": {
                "term": {"id": "ENVO:00000446", "name": "terrestrial biome"}
            },
            # Some samples already have partial weather data
            "temp": {
                "has_numeric_value": 22.0,
                "has_unit": "Celsius",
                "type": "nmdc:QuantityValue",
            },
        },
        {
            "id": "nmdc:bsm-11-demo002",
            "lat_lon": {"latitude": 36.7783, "longitude": -119.4179},
            "collection_date": {"has_raw_value": "2019-08-15"},
            "env_broad_scale": {
                "term": {"id": "ENVO:00000447", "name": "marine biome"}
            },
            # No existing weather data
        },
        {
            "id": "nmdc:bsm-11-demo003",
            "lat_lon": {"latitude": 40.7128, "longitude": -74.0060},
            "collection_date": {"has_raw_value": "2020-03-20T09:15Z"},
            "humidity": {
                "has_numeric_value": 65.0,
                "has_unit": "percent",
                "type": "nmdc:QuantityValue",
            },
        },
    ]

    gold_samples = [
        {
            "id": "Gb0demo001",
            "latitude": 47.6062,
            "longitude": -122.3321,
            "dateCollected": "2017-09-22",
            "geoLocation": "USA: Seattle, Washington",
            "sampleCollectionTemperature": "18.5 Celsius",
        },
        {
            "id": "Gb0demo002",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "dateCollected": "2018-06-05",
            "geoLocation": "UK: London",
            # No existing weather data
        },
    ]

    return {"nmdc": nmdc_samples, "gold": gold_samples}


def demonstrate_single_sample_enrichment():
    """Demonstrate weather enrichment for a single biosample."""

    print("🌤️  Single Sample Weather Enrichment Demo")
    print("=" * 50)

    # Create weather service with both providers
    weather_service = WeatherService()

    # Sample NMDC biosample
    sample = {
        "id": "nmdc:bsm-11-demo",
        "lat_lon": {"latitude": 42.5, "longitude": -85.4},
        "collection_date": {"has_raw_value": "2018-07-12T14:30Z"},
    }

    print(f"Original sample: {sample['id']}")
    print(
        f"Location: {sample['lat_lon']['latitude']}, {sample['lat_lon']['longitude']}"
    )
    print(f"Collection date: {sample['collection_date']['has_raw_value']}")
    print()

    # Perform weather enrichment
    try:
        result = weather_service.get_weather_for_biosample(sample, target_schema="nmdc")

        if result["enrichment_success"]:
            print("✅ Weather enrichment successful!")

            # Show weather data obtained
            weather_result = result["weather_result"]
            print(f"Temporal quality: {weather_result.overall_quality.value}")
            print(
                f"Successful providers: {', '.join(weather_result.successful_providers)}"
            )
            print()

            # Show enriched fields
            print("🌡️  Weather data retrieved:")
            if weather_result.temperature:
                temp_val = weather_result.temperature.value
                if isinstance(temp_val, dict):
                    print(
                        f"  Temperature: {temp_val['avg']:.1f}°C (range: {temp_val['min']:.1f}-{temp_val['max']:.1f}°C)"
                    )
                else:
                    print(f"  Temperature: {temp_val:.1f}°C")

            if weather_result.wind_speed:
                wind_val = weather_result.wind_speed.value
                wind_speed = wind_val["avg"] if isinstance(wind_val, dict) else wind_val
                print(
                    f"  Wind speed: {wind_speed:.1f} {weather_result.wind_speed.unit}"
                )

            if weather_result.wind_direction:
                print(f"  Wind direction: {weather_result.wind_direction.value:.0f}°")

            if weather_result.humidity:
                print(f"  Humidity: {weather_result.humidity.value:.1f}%")

            if weather_result.precipitation:
                print(f"  Precipitation: {weather_result.precipitation.value:.1f} mm")

            if weather_result.solar_radiation:
                print(
                    f"  Solar radiation: {weather_result.solar_radiation.value:.1f} W/m²"
                )

            print()

            # Show NMDC schema mapping
            print("📋 NMDC schema mapping:")
            schema_mapping = result["schema_mapping"]
            for field_name, field_data in schema_mapping.items():
                if isinstance(field_data, dict) and "has_numeric_value" in field_data:
                    print(
                        f"  {field_name}: {field_data['has_numeric_value']} {field_data.get('has_unit', '')}"
                    )
                elif isinstance(field_data, dict) and "has_raw_value" in field_data:
                    print(f"  {field_name}: {field_data['has_raw_value']}")

            print()

            # Show coverage metrics
            print("📊 Coverage metrics:")
            coverage = result["coverage_metrics"]
            print(
                f"  Fields enriched: {coverage['enriched_count']}/{coverage['total_possible_fields']}"
            )
            print(f"  Enrichment percentage: {coverage['enrichment_percentage']:.1f}%")
            print(
                f"  Average quality score: {coverage['average_quality_score']:.0f}/100"
            )

        else:
            print("❌ Weather enrichment failed")
            if "error" in result:
                print(f"Error: {result['error']}")

    except Exception as e:
        print(f"❌ Error during enrichment: {e}")


def demonstrate_multi_provider_comparison():
    """Demonstrate comparison between different weather providers."""

    print("\n🔄 Multi-Provider Comparison Demo")
    print("=" * 50)

    location = {"lat": 42.5, "lon": -85.4}
    target_date = date(2018, 7, 12)

    providers = [
        ("Open-Meteo", OpenMeteoProvider()),
        ("MeteoStat", MeteostatProvider()),
    ]

    print(f"Location: {location['lat']}, {location['lon']}")
    print(f"Date: {target_date}")
    print()

    for provider_name, provider in providers:
        print(f"🌐 Testing {provider_name}:")
        try:
            if provider.is_available(location["lat"], location["lon"], target_date):
                result = provider.get_daily_weather(
                    location["lat"], location["lon"], target_date
                )

                if result.successful_providers:
                    print(f"  ✅ Success - Quality: {result.overall_quality.value}")
                    if result.temperature:
                        temp_val = result.temperature.value
                        if isinstance(temp_val, dict):
                            print(
                                f"  🌡️  Temperature: {temp_val.get('avg', 'N/A'):.1f}°C"
                            )
                        else:
                            print(f"  🌡️  Temperature: {temp_val:.1f}°C")
                    if result.wind_speed:
                        wind_val = result.wind_speed.value
                        wind_speed = (
                            wind_val["avg"] if isinstance(wind_val, dict) else wind_val
                        )
                        print(f"  💨 Wind: {wind_speed:.1f} {result.wind_speed.unit}")
                else:
                    print("  ❌ No data available")
            else:
                print("  ⚠️  Provider not available for this date/location")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()


def demonstrate_coverage_metrics():
    """Demonstrate before/after coverage metrics analysis."""

    print("\n📈 Before/After Coverage Metrics Demo")
    print("=" * 50)

    # Create sample data
    biosamples = create_sample_biosamples()

    # Initialize metrics analyzer
    metrics_analyzer = WeatherEnrichmentMetrics()

    # Analyze coverage for each source
    analyses = []

    for source, samples in biosamples.items():
        print(f"Analyzing {source.upper()} samples ({len(samples)} samples)...")

        try:
            analysis = metrics_analyzer.analyze_biosample_collection(samples, source)
            analyses.append(analysis)

            print(f"✅ Analysis complete for {source}")

            # Show before/after summary
            improvements = analysis["improvements"]
            print("Before → After coverage:")

            for weather_param, improvement_data in improvements.items():
                before = improvement_data["before_coverage"]
                after = improvement_data["after_coverage"]
                delta = improvement_data["absolute_improvement"]
                category = improvement_data["improvement_category"]

                print(
                    f"  {weather_param}: {before:.1f}% → {after:.1f}% (+{delta:.1f}%) [{category}]"
                )

            print()

        except Exception as e:
            print(f"❌ Analysis failed for {source}: {e}")
            print()

    # Generate comprehensive report
    if analyses:
        print("📊 Comprehensive Metrics Report:")
        report_df = metrics_analyzer.generate_metrics_report(analyses)
        print(report_df.to_string(index=False))


def main():
    """Run all weather enrichment demonstrations."""

    print("🌤️  Weather Enrichment for Biosample Environmental Context")
    print("=" * 70)
    print("Demonstrates day-specific weather data enrichment using multiple providers")
    print("with temporal precision tracking and schema-aligned output.")
    print()

    try:
        # Run demonstrations
        demonstrate_single_sample_enrichment()
        demonstrate_multi_provider_comparison()
        demonstrate_coverage_metrics()

        print("\n✅ All demonstrations completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
