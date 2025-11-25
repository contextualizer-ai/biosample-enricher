#!/usr/bin/env python3
"""
Provider Comparison Example

Shows how to inspect metadata to compare results from different data providers.
Useful for understanding data quality and consistency.
"""

from biosample_enricher.submission_values import get_submission_values


def main():
    """Compare climate data from multiple providers."""
    # Boston coordinates
    lat = 42.3601
    lon = -71.0589

    print(f"Getting climate data for Boston ({lat}, {lon})...\n")

    # Get climate normals (automatically queries multiple providers)
    result = get_submission_values(
        lat=lat, lon=lon, slots=["annual_precpt", "annual_temp"]
    )

    # The "values" are consensus averages across providers
    values = result["values"]
    print("Consensus Values (averaged across providers):")
    print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year")
    print(f"  annual_temp: {values['annual_temp']:.1f} °C")
    print()

    # Inspect individual provider results
    metadata = result["metadata"]["climate_normals"]

    print("Individual Provider Results:")
    print(f"  Providers used: {', '.join(metadata['providers_used'])}")
    print()

    for provider_name, provider_data in metadata["provider_results"].items():
        print(f"  {provider_name}:")
        print(f"    annual_precpt: {provider_data['annual_precpt']:.1f} mm/year")
        print(f"    annual_temp: {provider_data['annual_temp']:.1f} °C")
        print(f"    period: {provider_data['period']}")

        if "station_distance_km" in provider_data:
            print(
                f"    station distance: {provider_data['station_distance_km']:.1f} km"
            )
        print()

    # Calculate variance between providers
    precip_values = [p["annual_precpt"] for p in metadata["provider_results"].values()]
    temp_values = [p["annual_temp"] for p in metadata["provider_results"].values()]

    precip_range = max(precip_values) - min(precip_values)
    temp_range = max(temp_values) - min(temp_values)

    print("Data Quality Metrics:")
    print(f"  Precipitation range: {precip_range:.1f} mm/year")
    print(f"  Temperature range: {temp_range:.1f} °C")
    print()

    if precip_range < 100:
        print("  ✓ Good agreement between providers on precipitation")
    else:
        print("  ⚠ Significant variance in precipitation estimates")

    if temp_range < 1:
        print("  ✓ Good agreement between providers on temperature")
    else:
        print("  ⚠ Significant variance in temperature estimates")


if __name__ == "__main__":
    main()
