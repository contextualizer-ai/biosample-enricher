#!/usr/bin/env python3
"""
Consensus Strategies Example

Shows how different consensus strategies affect multi-provider results.
When multiple providers return data, you can choose how to combine them.
"""

from biosample_enricher.environmental_metadata import (
    CONSENSUS_STRATEGIES,
    get_environmental_metadata,
)


def main() -> None:
    """Compare consensus strategies for elevation data."""
    # Mount Rainier area - known high elevation with multiple providers
    lat = 46.8523
    lon = -121.7603

    print(f"Comparing consensus strategies for Mount Rainier ({lat}, {lon})")
    print(f"Available strategies: {sorted(CONSENSUS_STRATEGIES)}\n")

    strategies_to_test = ["mean", "median", "first"]

    for strategy in strategies_to_test:
        print(f"\nStrategy: {strategy}")
        print("-" * 40)

        result = get_environmental_metadata(
            lat=lat,
            lon=lon,
            slots=["elev"],
            strategy=strategy,
        )

        values = result["values"]
        metadata = result.get("metadata", {})

        if "elev" in values:
            print(f"  Result: {values['elev']:.1f} m")

        # Show individual provider values for comparison
        if "elevation" in metadata and "provider_results" in metadata["elevation"]:
            print("  Provider values:")
            for provider, data in metadata["elevation"]["provider_results"].items():
                if "elev" in data:
                    print(f"    {provider}: {data['elev']:.1f} m")


def strategy_descriptions() -> None:
    """Print strategy descriptions."""
    print("\n" + "=" * 60)
    print("Consensus Strategy Guide")
    print("=" * 60)

    descriptions = {
        "mean": "Average of all provider values (default, most common)",
        "median": "Middle value when sorted - robust to outliers",
        "first": "Use first successful provider (fastest)",
        "best_quality": "Use provider with highest quality score",
    }

    print("\nWhen to use each:")
    for strategy, desc in descriptions.items():
        print(f"\n  {strategy}:")
        print(f"    {desc}")

    print("\nRecommendation: 'mean' (default) works well for most cases.")
    print("Use 'median' if you suspect outliers in provider data.")


if __name__ == "__main__":
    main()
    strategy_descriptions()
