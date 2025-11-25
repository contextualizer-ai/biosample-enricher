"""
Shared consensus strategies for combining values from multiple providers.

This module provides standardized functions for combining numeric values
from multiple data providers into a single consensus value. All services
(climate, elevation, weather, soil, marine) should use these functions
to ensure consistent behavior.

Consensus Strategies
--------------------
- **mean**: Simple arithmetic average of all values (default for most use cases)
- **median**: Middle value when sorted (robust to outliers)
- **first**: Use first successful provider in order
- **best_quality**: Use provider with best quality metric (e.g., closest station)

Examples
--------
>>> from biosample_enricher.consensus import compute_consensus
>>>
>>> # Average precipitation from multiple providers
>>> values = {"meteostat": 453.1, "nasa_power": 585.5}
>>> result = compute_consensus(values, strategy="mean")
>>> print(result)
{"value": 519.3, "strategy": "mean", "providers_used": ["meteostat", "nasa_power"]}
>>>
>>> # Use closest weather station
>>> values = {"station_a": 22.5, "station_b": 23.1}
>>> quality = {"station_a": 5.2, "station_b": 12.8}  # distance in km
>>> result = compute_consensus(values, strategy="best_quality", quality_scores=quality)
>>> print(result)
{"value": 22.5, "strategy": "best_quality", "providers_used": ["station_a"]}
"""

from enum import Enum
from statistics import mean, median
from typing import Any

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    "ConsensusStrategy",
    "compute_consensus",
    "STRATEGY_DESCRIPTIONS",
]


class ConsensusStrategy(str, Enum):
    """Available strategies for combining multi-provider values."""

    MEAN = "mean"  # Arithmetic average (default)
    MEDIAN = "median"  # Middle value (robust to outliers)
    FIRST = "first"  # First successful provider
    BEST_QUALITY = "best_quality"  # Provider with best quality metric


# Human-readable descriptions for documentation
STRATEGY_DESCRIPTIONS: dict[str, str] = {
    "mean": "Arithmetic average across all successful providers. "
    "Best for general use when providers have similar reliability.",
    "median": "Middle value when sorted. "
    "Robust to outliers - use when one provider might return anomalous values.",
    "first": "Use first successful provider in priority order. "
    "Fast, but depends on provider ordering.",
    "best_quality": "Use provider with best quality metric (e.g., closest station, "
    "highest resolution). Requires quality_scores parameter.",
}


def compute_consensus(
    provider_values: dict[str, float | None],
    strategy: str = "mean",
    quality_scores: dict[str, float] | None = None,
    lower_is_better: bool = True,
) -> dict[str, Any]:
    """
    Combine values from multiple providers using specified strategy.

    Args:
        provider_values: Dict mapping provider names to their values.
                        None values are treated as failures and excluded.
        strategy: One of "mean", "median", "first", "best_quality"
        quality_scores: For "best_quality" strategy, dict mapping provider names
                       to quality metrics (e.g., station distance, resolution)
        lower_is_better: For "best_quality", whether lower scores are better
                        (True for distance/error, False for confidence)

    Returns:
        Dict with:
        - value: The consensus value (float or None if no valid values)
        - strategy: The strategy used
        - providers_used: List of provider names that contributed
        - all_values: Dict of all provider values for transparency

    Raises:
        ValueError: If unknown strategy or best_quality without quality_scores

    Examples:
        >>> # Simple average
        >>> compute_consensus({"a": 10.0, "b": 20.0}, strategy="mean")
        {"value": 15.0, "strategy": "mean", "providers_used": ["a", "b"], ...}

        >>> # Median (robust to outliers)
        >>> compute_consensus({"a": 10.0, "b": 15.0, "c": 100.0}, strategy="median")
        {"value": 15.0, "strategy": "median", "providers_used": ["a", "b", "c"], ...}

        >>> # Best quality (closest station)
        >>> compute_consensus(
        ...     {"near": 22.5, "far": 23.1},
        ...     strategy="best_quality",
        ...     quality_scores={"near": 2.0, "far": 15.0},
        ...     lower_is_better=True
        ... )
        {"value": 22.5, "strategy": "best_quality", "providers_used": ["near"], ...}
    """
    # Filter to valid values
    valid_values = {k: v for k, v in provider_values.items() if v is not None}

    if not valid_values:
        return {
            "value": None,
            "strategy": strategy,
            "providers_used": [],
            "all_values": provider_values,
        }

    # Get ordered list of providers (preserves insertion order in Python 3.7+)
    providers = list(valid_values.keys())
    values = list(valid_values.values())

    if strategy == ConsensusStrategy.MEAN.value:
        consensus_value = mean(values)
        return {
            "value": round(consensus_value, 2),
            "strategy": "mean",
            "providers_used": providers,
            "all_values": provider_values,
        }

    elif strategy == ConsensusStrategy.MEDIAN.value:
        consensus_value = median(values)
        return {
            "value": round(consensus_value, 2),
            "strategy": "median",
            "providers_used": providers,
            "all_values": provider_values,
        }

    elif strategy == ConsensusStrategy.FIRST.value or strategy == "first_successful":
        # "first_successful" is an alias for "first"
        first_provider = providers[0]
        return {
            "value": valid_values[first_provider],
            "strategy": "first",
            "providers_used": [first_provider],
            "all_values": provider_values,
        }

    elif strategy == ConsensusStrategy.BEST_QUALITY.value:
        if not quality_scores:
            raise ValueError("best_quality strategy requires quality_scores parameter")

        # Filter quality scores to only valid providers
        valid_scores = {k: v for k, v in quality_scores.items() if k in valid_values}

        if not valid_scores:
            # Fall back to first if no quality scores for valid providers
            logger.warning(
                "No quality scores for valid providers, falling back to first"
            )
            first_provider = providers[0]
            return {
                "value": valid_values[first_provider],
                "strategy": "best_quality",
                "providers_used": [first_provider],
                "all_values": provider_values,
                "note": "Fell back to first - no quality scores available",
            }

        # Select best provider based on quality score
        if lower_is_better:
            best_provider = min(valid_scores, key=valid_scores.get)  # type: ignore
        else:
            best_provider = max(valid_scores, key=valid_scores.get)  # type: ignore

        return {
            "value": valid_values[best_provider],
            "strategy": "best_quality",
            "providers_used": [best_provider],
            "all_values": provider_values,
            "quality_score": valid_scores[best_provider],
        }

    else:
        valid_strategies = [s.value for s in ConsensusStrategy]
        raise ValueError(
            f"Unknown strategy: {strategy}. Valid strategies: {valid_strategies}"
        )
