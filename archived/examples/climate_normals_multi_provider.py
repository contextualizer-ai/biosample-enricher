#!/usr/bin/env python
"""
Demo: Multi-provider climate normals comparison.

Shows how to get climate normals from multiple providers and compare results.
"""

from biosample_enricher.weather.service import WeatherService


def main():
    """Demonstrate multi-provider climate normals retrieval."""
    service = WeatherService()

    # Example location: New York City
    lat, lon = 40.7128, -74.0060
    print(f"\n{'=' * 70}")
    print(f"Climate Normals for New York City ({lat}, {lon})")
    print(f"{'=' * 70}\n")

    # Get climate normals from ALL providers (default behavior)
    normals = service.get_climate_normals(lat, lon)

    print(f"Requested providers: {normals.requested_providers}")
    print(f"Successful providers: {normals.successful_providers}")
    if normals.failed_providers:
        print(f"Failed providers: {normals.failed_providers}")
    print()

    # Show results from each provider
    print("Results by Provider:")
    print("-" * 70)
    for provider_name in normals.successful_providers:
        result = normals.get_provider_result(provider_name)
        if result:
            annual_precip = result.get_annual_precipitation()
            annual_temp = result.get_annual_temperature()
            print(f"\n{provider_name.upper()}:")
            print(f"  Period: {result.normals_period[0]}-{result.normals_period[1]}")
            print(f"  Annual precipitation: {annual_precip:.1f} mm/year")
            print(f"  Annual temperature: {annual_temp:.1f}°C")
            if result.station_distance_km > 0:
                print(f"  Station distance: {result.station_distance_km:.1f} km")

    # Show consensus values
    print("\n" + "=" * 70)
    print("Consensus Values (averaged across all providers):")
    print("-" * 70)
    consensus = normals.to_submission_schema(strategy="consensus")
    print(f"Annual precipitation: {consensus['annual_precpt']:.1f} mm/year")
    print(f"Annual temperature: {consensus['annual_temp']:.1f}°C")

    # Show value ranges for detecting discrepancies
    print("\n" + "=" * 70)
    print("Value Ranges (for quality checking):")
    print("-" * 70)
    ranges = normals.get_value_ranges()
    if ranges["annual_precpt_range"]:
        min_p, max_p = ranges["annual_precpt_range"]
        print(f"Precipitation range: {min_p:.1f} - {max_p:.1f} mm/year")
        print(
            f"  Difference: {max_p - min_p:.1f} mm ({(max_p - min_p) / min_p * 100:.1f}%)"
        )

    if ranges["annual_temp_range"]:
        min_t, max_t = ranges["annual_temp_range"]
        print(f"Temperature range: {min_t:.1f} - {max_t:.1f}°C")
        print(f"  Difference: {max_t - min_t:.1f}°C")

    # Show how to get result from specific provider
    print("\n" + "=" * 70)
    print("Using Specific Provider:")
    print("-" * 70)
    meteostat_result = normals.get_provider_result("meteostat")
    if meteostat_result:
        schema_values = meteostat_result.to_submission_schema()
        print("Meteostat values:")
        print(f"  annual_precpt: {schema_values['annual_precpt']:.1f} mm")
        print(f"  annual_temp: {schema_values['annual_temp']:.1f}°C")
        print(f"  data_source: {schema_values['data_source']}")

    # Example: Query only specific providers
    print("\n" + "=" * 70)
    print("Query Specific Provider Only (NASA POWER):")
    print("-" * 70)
    nasa_only = service.get_climate_normals(lat, lon, providers=["nasa_power"])
    print(f"Successful providers: {nasa_only.successful_providers}")
    nasa_result = nasa_only.get_provider_result("nasa_power")
    if nasa_result:
        print(
            f"NASA POWER: {nasa_result.get_annual_precipitation():.1f} mm/year, "
            f"{nasa_result.get_annual_temperature():.1f}°C"
        )

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
