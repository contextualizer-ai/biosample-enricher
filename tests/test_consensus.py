"""Tests for the consensus module."""

import pytest

from biosample_enricher.consensus import (
    STRATEGY_DESCRIPTIONS,
    ConsensusStrategy,
    compute_consensus,
)


@pytest.mark.unit
class TestComputeConsensus:
    """Tests for compute_consensus function."""

    def test_mean_strategy_basic(self):
        """Test mean strategy with basic values."""
        provider_values = {"a": 10.0, "b": 20.0, "c": 30.0}
        result = compute_consensus(provider_values, strategy="mean")

        assert result["value"] == 20.0
        assert result["strategy"] == "mean"
        assert set(result["providers_used"]) == {"a", "b", "c"}

    def test_median_strategy_basic(self):
        """Test median strategy with basic values."""
        provider_values = {"a": 10.0, "b": 20.0, "c": 100.0}
        result = compute_consensus(provider_values, strategy="median")

        assert result["value"] == 20.0  # Middle value
        assert result["strategy"] == "median"
        assert set(result["providers_used"]) == {"a", "b", "c"}

    def test_first_strategy_basic(self):
        """Test first strategy returns first provider's value."""
        provider_values = {"first_provider": 10.0, "second": 20.0, "third": 30.0}
        result = compute_consensus(provider_values, strategy="first")

        assert result["value"] == 10.0
        assert result["strategy"] == "first"
        assert result["providers_used"] == ["first_provider"]

    def test_best_quality_strategy_lower_is_better(self):
        """Test best_quality strategy with lower_is_better=True."""
        provider_values = {"near": 22.5, "far": 23.1, "medium": 22.8}
        quality_scores = {"near": 2.0, "far": 15.0, "medium": 8.0}

        result = compute_consensus(
            provider_values,
            strategy="best_quality",
            quality_scores=quality_scores,
            lower_is_better=True,
        )

        assert result["value"] == 22.5  # "near" has lowest score
        assert result["strategy"] == "best_quality"
        assert result["providers_used"] == ["near"]

    def test_best_quality_strategy_higher_is_better(self):
        """Test best_quality strategy with lower_is_better=False."""
        provider_values = {"low_conf": 22.5, "high_conf": 23.1, "medium_conf": 22.8}
        quality_scores = {"low_conf": 0.3, "high_conf": 0.95, "medium_conf": 0.7}

        result = compute_consensus(
            provider_values,
            strategy="best_quality",
            quality_scores=quality_scores,
            lower_is_better=False,
        )

        assert result["value"] == 23.1  # "high_conf" has highest score
        assert result["strategy"] == "best_quality"
        assert result["providers_used"] == ["high_conf"]

    def test_best_quality_without_scores_raises_error(self):
        """Test best_quality strategy raises error without quality_scores."""
        provider_values = {"a": 10.0, "b": 20.0}

        with pytest.raises(ValueError, match="best_quality strategy requires"):
            compute_consensus(provider_values, strategy="best_quality")

    def test_invalid_strategy_raises_error(self):
        """Test invalid strategy raises ValueError."""
        provider_values = {"a": 10.0, "b": 20.0}

        with pytest.raises(ValueError, match="Unknown strategy"):
            compute_consensus(provider_values, strategy="invalid_strategy")

    def test_handles_none_values(self):
        """Test that None values are filtered out."""
        provider_values = {"a": 10.0, "b": None, "c": 20.0}
        result = compute_consensus(provider_values, strategy="mean")

        assert result["value"] == 15.0  # Only a and c contribute
        assert set(result["providers_used"]) == {"a", "c"}

    def test_all_none_values_returns_none(self):
        """Test that all None values returns None result."""
        provider_values = {"a": None, "b": None}
        result = compute_consensus(provider_values, strategy="mean")

        assert result["value"] is None
        assert result["providers_used"] == []

    def test_empty_dict_returns_none(self):
        """Test that empty dict returns None result."""
        result = compute_consensus({}, strategy="mean")

        assert result["value"] is None
        assert result["providers_used"] == []

    def test_single_value(self):
        """Test with single provider value."""
        provider_values = {"only": 42.0}
        result = compute_consensus(provider_values, strategy="mean")

        assert result["value"] == 42.0
        assert result["providers_used"] == ["only"]

    def test_mean_rounds_to_two_decimals(self):
        """Test that mean results are rounded to 2 decimal places."""
        provider_values = {"a": 10.333, "b": 20.666, "c": 30.999}
        result = compute_consensus(provider_values, strategy="mean")

        # (10.333 + 20.666 + 30.999) / 3 = 20.666
        assert result["value"] == 20.67

    def test_all_values_preserved_in_output(self):
        """Test that original provider values are preserved in output."""
        provider_values = {"a": 10.0, "b": None, "c": 20.0}
        result = compute_consensus(provider_values, strategy="mean")

        assert result["all_values"] == provider_values


@pytest.mark.unit
class TestStrategyDescriptions:
    """Tests for strategy descriptions."""

    def test_all_strategies_have_descriptions(self):
        """Test all ConsensusStrategy values have descriptions."""
        for strategy in ConsensusStrategy:
            assert strategy.value in STRATEGY_DESCRIPTIONS
            assert len(STRATEGY_DESCRIPTIONS[strategy.value]) > 0

    def test_descriptions_are_strings(self):
        """Test all descriptions are non-empty strings."""
        for _strategy, description in STRATEGY_DESCRIPTIONS.items():
            assert isinstance(description, str)
            assert len(description) > 10  # Minimum reasonable description length
