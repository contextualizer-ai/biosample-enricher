#!/usr/bin/env python3
"""
Multiple Slot Types Example

Get climate data AND elevation in a single call.
Shows how to mix different types of submission-schema slots.
"""

from biosample_enricher.environmental_metadata import get_environmental_metadata


def main():
    """Get climate and elevation for Mount Rainier National Park."""
    # Mount Rainier Paradise visitor center
    lat = 46.7867
    lon = -121.7365

    print(f"Getting data for Mount Rainier area ({lat}, {lon})...\n")

    # Get climate + elevation together
    result = get_environmental_metadata(
        lat=lat, lon=lon, slots=["annual_precpt", "annual_temp", "elev"]
    )

    values = result["values"]

    # Display results
    print("NMDC Submission Values:")
    print(f"  elev: {values['elev']:.1f} m")
    print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year")
    print(f"  annual_temp: {values['annual_temp']:.1f} °C")

    print("\nNote: Climate data is 30-year average for the coordinates.")
    print("Elevation is precise for this location.")


if __name__ == "__main__":
    main()
