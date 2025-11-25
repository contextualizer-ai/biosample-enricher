#!/usr/bin/env python3
"""
Basic Climate Data Example

Get 30-year climate averages (annual_precpt, annual_temp) for a location.
This is the simplest and most common use case.
"""

from biosample_enricher.submission_values import get_submission_values


def main():
    """Get climate normals for San Francisco."""
    # San Francisco coordinates
    lat = 37.7749
    lon = -122.4194

    print(f"Getting climate data for San Francisco ({lat}, {lon})...\n")

    # Get annual precipitation and temperature
    result = get_submission_values(
        lat=lat, lon=lon, slots=["annual_precpt", "annual_temp"]
    )

    # Extract the values
    values = result["values"]

    # Display results
    print("NMDC Submission Values:")
    print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year")
    print(f"  annual_temp: {values['annual_temp']:.1f} °C")

    # Show which data providers were used
    metadata = result["metadata"]["climate_normals"]
    print(f"\nData sources: {', '.join(metadata['providers_used'])}")


if __name__ == "__main__":
    main()
