"""
Weather enrichment module for biosample environmental context.

Provides day-specific weather data from multiple providers with temporal precision tracking
and standardized output schema for NMDC/GOLD biosample enrichment.
"""

from biosample_enricher.weather.models import (
    TemporalPrecision,
    WeatherObservation,
    WeatherResult,
)
from biosample_enricher.weather.providers import MeteostatProvider, OpenMeteoProvider
from biosample_enricher.weather.service import WeatherService

__all__ = [
    "WeatherResult",
    "WeatherObservation",
    "TemporalPrecision",
    "OpenMeteoProvider",
    "MeteostatProvider",
    "WeatherService",
]
