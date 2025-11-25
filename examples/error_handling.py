#!/usr/bin/env python3
"""
Error Handling Example

Shows how to gracefully handle invalid inputs and missing data.
"""

from biosample_enricher.submission_values import (
    ALL_SUPPORTED_SLOTS,
    get_submission_values,
)


def example_invalid_coordinates():
    """Handle out-of-range coordinates."""
    print("Example 1: Invalid coordinates\n")

    try:
        get_submission_values(
            lat=999,  # Invalid: must be -90 to 90
            lon=-122.4194,
            slots=["annual_precpt"],
        )
    except ValueError as e:
        print(f"✗ Error caught: {e}\n")


def example_invalid_slot():
    """Handle unsupported slot names."""
    print("Example 2: Invalid slot name\n")

    try:
        get_submission_values(
            lat=37.7749, lon=-122.4194, slots=["annual_precpt", "invalid_slot_name"]
        )
    except ValueError as e:
        print(f"✗ Error caught: {e}")
        print("(Error message includes list of supported slots)\n")


def example_missing_data():
    """Handle slots that return no data."""
    print("Example 3: Missing data for a slot\n")

    # Requesting depth data for a land location
    result = get_submission_values(
        lat=37.7749,  # San Francisco (on land)
        lon=-122.4194,
        slots=["annual_precpt", "depth"],  # depth won't be available on land
    )

    values = result["values"]

    # Check each slot
    if "annual_precpt" in values:
        print(f"✓ annual_precpt: {values['annual_precpt']:.1f} mm/year")
    else:
        print("✗ annual_precpt: not available")

    if "depth" in values:
        print(f"✓ depth: {values['depth']} m")
    else:
        print("✗ depth: not available (expected - we're on land)")

    print()


def example_checking_supported_slots():
    """Show available slots before making request."""
    print("Example 4: Check supported slots\n")

    print(f"Total supported slots: {len(ALL_SUPPORTED_SLOTS)}")
    print(f"Slots: {sorted(ALL_SUPPORTED_SLOTS)[:5]}...")  # Show first 5
    print("(See documentation for complete list)\n")


def main():
    """Run all error handling examples."""
    print("=" * 70)
    print("Error Handling Examples")
    print("=" * 70)
    print()

    example_invalid_coordinates()
    example_invalid_slot()
    example_missing_data()
    example_checking_supported_slots()

    print("=" * 70)
    print("Key Takeaways:")
    print("  1. ValueError is raised for invalid inputs")
    print("  2. Missing slots are omitted from results (not set to None)")
    print("  3. Always check 'if slot_name in result[\"values\"]'")
    print("=" * 70)


if __name__ == "__main__":
    main()
