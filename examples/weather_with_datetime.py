#!/usr/bin/env python3
"""
Weather Data Example

Get point-in-time weather data for a specific collection date.
Weather slots like temp, humidity, wind_speed require a datetime parameter.
"""

from datetime import datetime

from biosample_enricher.submission_values import get_submission_values


def main() -> None:
    """Get weather data for Los Angeles on a specific date."""
    # Los Angeles coordinates
    lat = 34.0522
    lon = -118.2437

    # Sample collection date/time
    collection_datetime = datetime(2023, 7, 15, 14, 30)  # July 15, 2023 at 2:30 PM

    print(f"Getting weather data for Los Angeles ({lat}, {lon})")
    print(f"Collection datetime: {collection_datetime.isoformat()}\n")

    # Get weather data - datetime_obj is REQUIRED for weather slots
    result = get_submission_values(
        lat=lat,
        lon=lon,
        slots=["temp", "humidity", "wind_speed"],
        datetime_obj=collection_datetime,  # Required for weather slots!
    )

    values = result["values"]

    # Display results (not all slots may return data)
    print("NMDC Submission Values:")
    if "temp" in values:
        print(f"  temp: {values['temp']:.1f} °C")
    else:
        print("  temp: not available")

    if "humidity" in values:
        print(f"  humidity: {values['humidity']}")
    else:
        print("  humidity: not available")

    if "wind_speed" in values:
        print(f"  wind_speed: {values['wind_speed']}")
    else:
        print("  wind_speed: not available")

    print(
        "\nNote: Weather data availability depends on location and historical records."
    )


def compare_weather_and_climate() -> None:
    """Show the difference between weather (point-in-time) and climate (30-year avg)."""
    lat = 33.4484  # Phoenix, AZ
    lon = -112.0740
    summer_date = datetime(2023, 7, 15)  # Hot summer day

    print("\n" + "=" * 60)
    print("Comparing Weather vs Climate for Phoenix, AZ")
    print("=" * 60 + "\n")

    result = get_submission_values(
        lat=lat,
        lon=lon,
        slots=["annual_temp", "temp"],  # annual_temp = climate, temp = weather
        datetime_obj=summer_date,
    )

    values = result["values"]

    if "annual_temp" in values:
        print(f"annual_temp (30-year average): {values['annual_temp']:.1f} °C")
    if "temp" in values:
        print(f"temp (July 15, 2023):          {values['temp']:.1f} °C")

    if "annual_temp" in values and "temp" in values:
        diff = values["temp"] - values["annual_temp"]
        print(f"\nDifference: {diff:+.1f} °C")
        print("(Summer day is hotter than annual average, as expected)")


if __name__ == "__main__":
    main()
    compare_weather_and_climate()
