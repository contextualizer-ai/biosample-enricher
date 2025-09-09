"""Biosample Enricher: Infer AI-friendly metadata about biosamples from multiple sources."""

__version__ = "0.1.0"

from .core import BiosampleEnricher
from .models import BiosampleMetadata

__all__ = ["BiosampleEnricher", "BiosampleMetadata"]
