"""Tests for submission_values slot and provider validation."""

import pytest

from biosample_enricher.submission_values import (
    ALL_SUPPORTED_SLOTS,
    CLIMATE_PROVIDERS,
    CLIMATE_SLOTS,
    get_submission_values,
)


def test_invalid_slot_raises_error():
    """Test that invalid slot names raise ValueError with helpful message."""
    with pytest.raises(ValueError, match="Unsupported slot.*invalid_slot_name"):
        get_submission_values(
            lat=37.7749,
            lon=-122.4194,
            slots=["annual_precpt", "invalid_slot_name"],
        )


def test_invalid_climate_provider_raises_error():
    """Test that invalid climate provider names raise ValueError."""
    with pytest.raises(ValueError, match="Invalid climate provider.*invalid_provider"):
        get_submission_values(
            lat=37.7749,
            lon=-122.4194,
            slots=["annual_precpt"],
            providers=["invalid_provider"],
        )


def test_constants_are_accessible():
    """Test that slot and provider constants are publicly accessible."""
    assert "annual_precpt" in CLIMATE_SLOTS
    assert "annual_temp" in CLIMATE_SLOTS
    assert "meteostat" in CLIMATE_PROVIDERS
    assert "nasa_power" in CLIMATE_PROVIDERS
    assert len(ALL_SUPPORTED_SLOTS) > 0


def test_valid_climate_providers_accepted():
    """Test that valid climate providers don't raise errors."""
    # Should not raise - just testing validation, not actual API calls
    # (will fail later when trying to connect, but validation should pass)
    try:
        get_submission_values(
            lat=37.7749,
            lon=-122.4194,
            slots=["annual_precpt"],
            providers=["meteostat"],
        )
    except ValueError as e:
        # If ValueError is raised, it should NOT be about invalid providers
        assert "Invalid climate provider" not in str(e)
    except Exception:
        # Other exceptions are fine (network, API, etc.) - we're just testing validation
        pass


def test_helpful_error_message_shows_available_options():
    """Test that error messages include available slots/providers."""
    with pytest.raises(ValueError) as exc_info:
        get_submission_values(
            lat=37.7749,
            lon=-122.4194,
            slots=["invalid_slot"],
        )

    error_msg = str(exc_info.value)
    assert "Supported slots:" in error_msg
    assert "annual_precpt" in error_msg or "annual_temp" in error_msg


def test_empty_slots_raises_error():
    """Test that empty slots list raises ValueError."""
    with pytest.raises(ValueError, match="slots list cannot be empty"):
        get_submission_values(
            lat=37.7749,
            lon=-122.4194,
            slots=[],
        )
